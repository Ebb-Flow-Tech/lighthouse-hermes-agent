# gateway/platforms/lark.py
"""Lark platform adapter for hermes-agent gateway.

Handles Lark webhook events, sends Interactive Message Cards,
and manages event deduplication and signature verification.
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from base64 import b64decode
from typing import Any, Dict, List, Optional, Tuple

import httpx
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding

from gateway.platforms.base import BasePlatformAdapter, SendResult, MessageEvent, MessageType
from gateway.platforms.lark_cards import (
    build_chart_card,
    build_error_card,
    build_insight_card,
    build_table_card,
    build_thinking_card,
)
from gateway.config import Platform, PlatformConfig

logger = logging.getLogger(__name__)

# Lark API base URL
LARK_API_BASE = "https://open.larksuite.com/open-apis"

# Concurrency limit
MAX_CONCURRENT = 5

# Event dedup TTL (5 minutes)
EVENT_DEDUP_TTL = 300


def check_lark_requirements() -> bool:
    """Verify Lark dependencies are available."""
    try:
        import httpx  # noqa: F401
        import cryptography  # noqa: F401
        return True
    except ImportError:
        return False


class LarkAdapter(BasePlatformAdapter):
    """Lark platform adapter using Interactive Message Cards."""

    MAX_MESSAGE_LENGTH = 30000  # Lark card content limit

    def __init__(self, config: PlatformConfig) -> None:
        super().__init__(config, Platform.LARK)
        self._app_id: str = config.extra.get("app_id", "")
        self._app_secret: str = config.extra.get("app_secret", "")
        self._verification_token: str = config.extra.get("verification_token", "")
        self._encrypt_key: str = config.extra.get("encrypt_key", "")
        self._tenant_access_token: str = ""
        self._token_expires_at: float = 0
        self._seen_events: dict[str, float] = {}
        self._active_calls = 0
        self._http: Optional[httpx.AsyncClient] = None
        self._thinking_messages: dict[str, str] = {}  # chat_id -> message_id

    @property
    def name(self) -> str:
        return "Lark"

    async def connect(self) -> bool:
        """Initialize HTTP client and obtain tenant access token."""
        self._http = httpx.AsyncClient(timeout=30)
        try:
            await self._refresh_token()
            self._mark_connected()
            logger.info("Lark adapter connected (app_id=%s)", self._app_id[:8])
            return True
        except Exception as e:
            logger.error("Lark connection failed: %s", e)
            return False

    async def disconnect(self) -> None:
        """Close HTTP client."""
        self._mark_disconnected()
        if self._http:
            await self._http.aclose()
            self._http = None

    # ---- Token Management ----

    async def _refresh_token(self) -> None:
        """Obtain or refresh tenant access token from Lark."""
        if self._http is None:
            return
        resp = await self._http.post(
            f"{LARK_API_BASE}/auth/v3/tenant_access_token/internal",
            json={"app_id": self._app_id, "app_secret": self._app_secret},
        )
        data = resp.json()
        self._tenant_access_token = data.get("tenant_access_token", "")
        expire = data.get("expire", 7200)
        self._token_expires_at = time.time() + expire - 300

    async def _ensure_token(self) -> str:
        """Ensure tenant access token is valid, refresh if needed."""
        if time.time() >= self._token_expires_at:
            await self._refresh_token()
        return self._tenant_access_token

    async def _lark_request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make authenticated request to Lark API."""
        if self._http is None:
            raise RuntimeError("Not connected")
        token = await self._ensure_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        resp = await self._http.request(
            method, f"{LARK_API_BASE}{path}", headers=headers, **kwargs
        )
        return resp.json()

    # ---- Sending Methods ----

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        """Send content as a Lark Interactive Card."""
        images, clean_text = self.extract_images(content)

        if self._has_markdown_table(clean_text):
            table = self._parse_markdown_table(clean_text)
            if table:
                card = build_table_card(
                    title=table["title"],
                    columns=table["columns"],
                    rows=table["rows"],
                    total_rows=len(table["rows"]),
                )
            else:
                card = build_insight_card(clean_text)
        elif images:
            # images is list of (url, alt_text) tuples
            image_url = images[0][0]
            image_key = await self._upload_image_from_url(image_url)
            caption = clean_text[:100] if clean_text else None
            card = build_chart_card(image_key=image_key, title=caption)
        else:
            card = build_insight_card(clean_text)

        # If we have a thinking message for this chat, update it in-place
        thinking_msg_id = self._thinking_messages.pop(chat_id, None)
        if thinking_msg_id:
            await self._update_card(thinking_msg_id, card)
            return SendResult(success=True, message_id=thinking_msg_id)

        msg_id = await self._send_card(chat_id, card)
        return SendResult(success=True, message_id=msg_id)

    async def send_typing(self, chat_id: str, metadata=None) -> None:
        """Send a thinking card and store message_id for later update."""
        card = build_thinking_card()
        msg_id = await self._send_card(chat_id, card)
        self._thinking_messages[chat_id] = msg_id

    async def send_image(
        self,
        chat_id: str,
        image_url: str,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> SendResult:
        """Upload image to Lark and send as chart card."""
        image_key = await self._upload_image_from_url(image_url)
        card = build_chart_card(image_key=image_key, title=caption)
        msg_id = await self._send_card(chat_id, card)
        return SendResult(success=True, message_id=msg_id)

    async def edit_message(
        self,
        chat_id: str,
        message_id: str,
        content: str,
    ) -> SendResult:
        """Update an existing card in-place."""
        images, clean_text = self.extract_images(content)

        if self._has_markdown_table(clean_text):
            table = self._parse_markdown_table(clean_text)
            if table:
                card = build_table_card(
                    title=table["title"],
                    columns=table["columns"],
                    rows=table["rows"],
                    total_rows=len(table["rows"]),
                )
            else:
                card = build_insight_card(clean_text)
        elif images:
            image_url = images[0][0]
            image_key = await self._upload_image_from_url(image_url)
            card = build_chart_card(image_key=image_key, title=clean_text[:100] or None)
        else:
            card = build_insight_card(clean_text)

        await self._update_card(message_id, card)
        return SendResult(success=True, message_id=message_id)

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """Fetch Lark chat metadata."""
        data = await self._lark_request("GET", f"/im/v1/chats/{chat_id}")
        chat = data.get("data", {})
        return {
            "name": chat.get("name", "Unknown"),
            "type": chat.get("chat_type", "group"),
            "chat_id": chat_id,
        }

    # ---- Lark API Helpers ----

    async def _send_card(self, chat_id: str, card: dict[str, Any]) -> str:
        """Send an Interactive Card to a Lark chat. Returns message_id."""
        data = await self._lark_request(
            "POST",
            "/im/v1/messages",
            params={"receive_id_type": "chat_id"},
            json={
                "receive_id": chat_id,
                "msg_type": "interactive",
                "content": json.dumps(card),
            },
        )
        return data.get("data", {}).get("message_id", "")

    async def _update_card(self, message_id: str, card: dict[str, Any]) -> None:
        """Update an existing Lark message card in-place."""
        await self._lark_request(
            "PATCH",
            f"/im/v1/messages/{message_id}",
            json={"content": json.dumps(card)},
        )

    async def _upload_image_from_url(self, url: str) -> str:
        """Download image from URL and upload to Lark, returning image_key."""
        if self._http is None:
            return ""
        resp = await self._http.get(url)
        return await self._upload_image_bytes(resp.content)

    async def _upload_image_bytes(self, image_bytes: bytes) -> str:
        """Upload image bytes to Lark and return image_key."""
        if self._http is None:
            return ""
        token = await self._ensure_token()
        resp = await self._http.post(
            f"{LARK_API_BASE}/im/v1/images",
            headers={"Authorization": f"Bearer {token}"},
            data={"image_type": "message"},
            files={"image": ("chart.png", image_bytes, "image/png")},
        )
        return resp.json().get("data", {}).get("image_key", "")

    # ---- Webhook Handling ----

    def _verify_signature(self, signature: str, timestamp: str, nonce: str, body: str) -> bool:
        """Verify Lark webhook signature (SHA256)."""
        if not self._encrypt_key:
            return True
        content = timestamp + nonce + self._encrypt_key + body
        expected = hashlib.sha256(content.encode()).hexdigest()
        return signature == expected

    def _decrypt_event(self, encrypt: str) -> str:
        """Decrypt AES-256-CBC encrypted Lark event."""
        key = hashlib.sha256(self._encrypt_key.encode()).digest()
        ciphertext = b64decode(encrypt)
        iv = ciphertext[:16]
        encrypted = ciphertext[16:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(encrypted) + decryptor.finalize()
        unpadder = sym_padding.PKCS7(128).unpadder()
        decrypted = unpadder.update(padded) + unpadder.finalize()
        return decrypted.decode("utf-8")

    def _is_duplicate(self, event_id: str) -> bool:
        """Check if event has been seen before (5-minute window)."""
        now = time.time()
        # Prune expired entries
        self._seen_events = {
            eid: ts for eid, ts in self._seen_events.items()
            if now - ts < EVENT_DEDUP_TTL
        }
        if event_id in self._seen_events:
            return True
        self._seen_events[event_id] = now
        return False

    def _has_markdown_table(self, text: str) -> bool:
        """Detect if text contains a markdown table."""
        return bool(re.search(r"\|.+\|.*\n\|[\s\-:|]+\|", text))

    def _parse_markdown_table(self, text: str) -> Optional[dict[str, Any]]:
        """Parse markdown table into columns and rows."""
        lines = text.strip().split("\n")
        table_start = -1
        for i, line in enumerate(lines):
            if "|" in line and i + 1 < len(lines) and re.match(r"\|[\s\-:|]+\|", lines[i + 1]):
                table_start = i
                break
        if table_start < 0:
            return None

        title_lines = [l.strip() for l in lines[:table_start] if l.strip()]
        title = title_lines[-1] if title_lines else "Query Results"
        title = title.strip("*").strip("#").strip()

        header_line = lines[table_start]
        columns = [c.strip() for c in header_line.strip("|").split("|") if c.strip()]

        rows: list[dict[str, Any]] = []
        for line in lines[table_start + 2:]:
            if "|" not in line:
                break
            values = [v.strip() for v in line.strip("|").split("|")]
            row = {}
            for j, col in enumerate(columns):
                row[col] = values[j] if j < len(values) else ""
            rows.append(row)

        return {"title": title, "columns": columns, "rows": rows}

    async def handle_webhook(self, raw_body: str, headers: dict[str, str]) -> dict[str, Any]:
        """Process an incoming Lark webhook event."""
        body = json.loads(raw_body)

        # Signature verification
        signature = headers.get("x-lark-signature", "")
        if signature and self._encrypt_key:
            timestamp = headers.get("x-lark-request-timestamp", "")
            nonce = headers.get("x-lark-request-nonce", "")
            if not self._verify_signature(signature, timestamp, nonce, raw_body):
                logger.warning("Lark signature verification failed")
                return {"error": "Unauthorized"}

        # Decrypt if encrypted
        if "encrypt" in body and self._encrypt_key:
            body = json.loads(self._decrypt_event(body["encrypt"]))

        # URL verification challenge
        if body.get("type") == "url_verification":
            return {"challenge": body.get("challenge", "")}

        # Token verification
        token = body.get("header", {}).get("token")
        if token != self._verification_token:
            logger.warning("Lark token mismatch")
            return {"error": "Unauthorized"}

        event_type = body.get("header", {}).get("event_type", "")
        event_id = body.get("header", {}).get("event_id", "")

        if not event_id or not event_type:
            return {"ok": True}

        # Deduplication
        if self._is_duplicate(event_id):
            return {"ok": True}

        # Handle events
        if event_type == "im.message.receive_v1":
            event = body.get("event", {})
            message = event.get("message", {})
            chat_id = message.get("chat_id", "")
            msg_type = message.get("message_type", "")

            if chat_id and msg_type == "text":
                try:
                    text = json.loads(message.get("content", "{}")).get("text", "")
                except (json.JSONDecodeError, TypeError):
                    text = ""

                if text.strip():
                    if self._active_calls >= MAX_CONCURRENT:
                        busy_card = build_error_card(
                            "I'm busy right now. Please try again in a moment."
                        )
                        await self._send_card(chat_id, busy_card)
                        return {"ok": True}

                    source = self.build_source(
                        chat_id=chat_id,
                        user_id=event.get("sender", {}).get("sender_id", {}).get("open_id", "unknown"),
                        user_name="Lark User",
                    )
                    msg_event = MessageEvent(
                        text=text,
                        message_type=MessageType.TEXT,
                        source=source,
                        message_id=message.get("message_id"),
                    )
                    asyncio.create_task(
                        self._process_message_async(msg_event, chat_id)
                    )

        elif event_type == "im.chat.member.bot.added_v1":
            chat_id = body.get("event", {}).get("chat_id", "")
            if chat_id:
                welcome = build_insight_card(
                    "**Hi! I'm Hermes, your data assistant.**\n\n"
                    "Ask me anything about your data \u2014 I can query databases, "
                    "run reports, and create charts.\n\n"
                    'Try: "Show me the top 10 orders this month"'
                )
                await self._send_card(chat_id, welcome)

        return {"ok": True}

    async def _process_message_async(self, event: MessageEvent, chat_id: str) -> None:
        """Process a message in the background with concurrency tracking."""
        self._active_calls += 1
        try:
            await self.send_typing(chat_id)
            await self.handle_message(event)
        except Exception as e:
            logger.error("Lark message processing error: %s", e)
            error_card = build_error_card(
                "Something went wrong. Please try again.",
                original_message=event.text,
            )
            thinking_msg_id = self._thinking_messages.pop(chat_id, None)
            if thinking_msg_id:
                await self._update_card(thinking_msg_id, error_card)
            else:
                await self._send_card(chat_id, error_card)
        finally:
            self._active_calls -= 1

    async def handle_card_action(self, body: dict[str, Any]) -> dict[str, Any]:
        """Handle Lark card action callbacks (e.g., Try again button)."""
        action = body.get("action", {}).get("value", {})
        if action.get("action") == "retry" and action.get("message"):
            chat_id = body.get("open_chat_id", "")
            if chat_id:
                source = self.build_source(
                    chat_id=chat_id,
                    user_id="retry",
                    user_name="Lark User",
                )
                msg_event = MessageEvent(
                    text=action["message"],
                    message_type=MessageType.TEXT,
                    source=source,
                )
                asyncio.create_task(
                    self._process_message_async(msg_event, chat_id)
                )
        return {}
