# tests/gateway/test_lark_cards.py
import json
import pytest
from gateway.platforms.lark_cards import (
    build_thinking_card,
    build_table_card,
    build_insight_card,
    build_chart_card,
    build_error_card,
)


class TestThinkingCard:
    def test_contains_analyzing_text(self):
        card = build_thinking_card()
        card_json = json.dumps(card)
        assert "Analyzing" in card_json

    def test_has_elements(self):
        card = build_thinking_card()
        assert "elements" in card

    def test_has_wide_screen_mode(self):
        card = build_thinking_card()
        assert card["config"]["wide_screen_mode"] is True


class TestTableCard:
    def test_builds_with_data(self):
        card = build_table_card(
            title="Top Orders",
            columns=["id", "name", "total"],
            rows=[
                {"id": 1, "name": "Order A", "total": 100},
                {"id": 2, "name": "Order B", "total": 200},
            ],
            total_rows=50,
        )
        card_json = json.dumps(card)
        assert "Top Orders" in card_json
        assert "elements" in card

    def test_truncates_to_20_rows(self):
        rows = [{"id": i} for i in range(30)]
        card = build_table_card(
            title="Test",
            columns=["id"],
            rows=rows,
            total_rows=30,
        )
        card_json = json.dumps(card)
        assert "20" in card_json
        assert "30" in card_json

    def test_shows_truncation_note(self):
        rows = [{"id": i} for i in range(25)]
        card = build_table_card(
            title="Test",
            columns=["id"],
            rows=rows,
            total_rows=25,
        )
        card_json = json.dumps(card)
        assert "Showing" in card_json

    def test_no_truncation_note_for_small_results(self):
        card = build_table_card(
            title="Test",
            columns=["id"],
            rows=[{"id": 1}, {"id": 2}],
            total_rows=2,
        )
        card_json = json.dumps(card)
        assert "Showing" not in card_json

    def test_optional_report_url(self):
        card = build_table_card(
            title="Test",
            columns=["id"],
            rows=[{"id": 1}],
            total_rows=1,
            report_url="https://example.com/report/1",
        )
        card_json = json.dumps(card)
        assert "View full report" in card_json


class TestInsightCard:
    def test_renders_markdown(self):
        card = build_insight_card("Revenue is up **23%** this month.")
        assert card["elements"][0]["content"] == "Revenue is up **23%** this month."

    def test_has_wide_screen_mode(self):
        card = build_insight_card("test")
        assert card["config"]["wide_screen_mode"] is True


class TestChartCard:
    def test_contains_image_key(self):
        card = build_chart_card(image_key="img_abc123", title="Revenue Trend")
        card_json = json.dumps(card)
        assert "img_abc123" in card_json

    def test_optional_title(self):
        card = build_chart_card(image_key="img_abc123")
        card_json = json.dumps(card)
        assert "img_abc123" in card_json

    def test_title_in_output(self):
        card = build_chart_card(image_key="img_abc123", title="Revenue Trend")
        card_json = json.dumps(card)
        assert "Revenue Trend" in card_json


class TestErrorCard:
    def test_contains_error_message(self):
        card = build_error_card(
            message="Connection failed",
            original_message="show me data",
        )
        card_json = json.dumps(card)
        assert "Connection failed" in card_json

    def test_retry_button_when_original_message_provided(self):
        card = build_error_card(
            message="Failed",
            original_message="show me data",
        )
        card_json = json.dumps(card)
        assert "Try again" in card_json
        assert "retry" in card_json

    def test_no_retry_button_without_original_message(self):
        card = build_error_card(message="Failed")
        card_json = json.dumps(card)
        assert "Try again" not in card_json
