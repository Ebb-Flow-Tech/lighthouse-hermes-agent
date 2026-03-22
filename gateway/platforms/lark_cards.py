# gateway/platforms/lark_cards.py
"""Lark Interactive Message Card builders.

Ported from packages/hermes/src/cards/ (TypeScript).
Each function returns a dict representing a Lark Interactive Card JSON structure.
"""

from typing import Any, Optional

MAX_DISPLAY_ROWS = 20


def build_thinking_card() -> dict[str, Any]:
    """Placeholder card shown while the agent is processing."""
    return {
        "config": {"wide_screen_mode": True},
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "plain_text",
                    "content": "\u23f3 Analyzing your question...",
                },
            },
        ],
    }


def build_table_card(
    *,
    title: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    total_rows: int,
    report_url: Optional[str] = None,
) -> dict[str, Any]:
    """Structured data table card with optional truncation note and report link."""
    display_rows = rows[:MAX_DISPLAY_ROWS]
    truncated = len(rows) > MAX_DISPLAY_ROWS or total_rows > len(display_rows)

    header_cols = [
        {
            "tag": "column",
            "width": "weighted",
            "weight": 1,
            "elements": [{"tag": "markdown", "content": f"**{col}**"}],
        }
        for col in columns
    ]

    data_rows = [
        {
            "tag": "column_set",
            "flex_mode": "none",
            "columns": [
                {
                    "tag": "column",
                    "width": "weighted",
                    "weight": 1,
                    "elements": [
                        {"tag": "markdown", "content": str(row.get(col, ""))}
                    ],
                }
                for col in columns
            ],
        }
        for row in display_rows
    ]

    elements: list[dict[str, Any]] = [
        {"tag": "markdown", "content": f"**{title}**"},
        {"tag": "hr"},
        {"tag": "column_set", "flex_mode": "none", "columns": header_cols},
        *data_rows,
    ]

    if truncated:
        elements.append(
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": f"Showing {len(display_rows)} of {total_rows} results",
                    }
                ],
            }
        )

    if report_url:
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "plain_text",
                            "content": "View full report in Lighthouse",
                        },
                        "type": "primary",
                        "url": report_url,
                    }
                ],
            }
        )

    return {"config": {"wide_screen_mode": True}, "elements": elements}


def build_insight_card(text: str) -> dict[str, Any]:
    """Markdown text card for analysis and insights."""
    return {
        "config": {"wide_screen_mode": True},
        "elements": [{"tag": "markdown", "content": text}],
    }


def build_chart_card(
    *,
    image_key: str,
    title: Optional[str] = None,
) -> dict[str, Any]:
    """Chart image card with optional title."""
    elements: list[dict[str, Any]] = []

    if title:
        elements.append({"tag": "markdown", "content": f"**{title}**"})

    elements.append(
        {
            "tag": "img",
            "img_key": image_key,
            "alt": {"tag": "plain_text", "content": title or "Chart"},
        }
    )

    return {"config": {"wide_screen_mode": True}, "elements": elements}


def build_error_card(
    message: str,
    original_message: Optional[str] = None,
) -> dict[str, Any]:
    """Error card with optional retry button."""
    elements: list[dict[str, Any]] = [
        {"tag": "markdown", "content": f"\u274c **Error:** {message}"},
    ]

    if original_message:
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "Try again"},
                        "type": "default",
                        "value": {
                            "action": "retry",
                            "message": original_message,
                        },
                    }
                ],
            }
        )

    return {"config": {"wide_screen_mode": True}, "elements": elements}
