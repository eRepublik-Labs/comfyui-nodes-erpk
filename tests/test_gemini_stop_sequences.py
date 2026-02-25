# ABOUTME: Tests for Gemini stop sequence parsing and validation.
# ABOUTME: Ensures the 5-sequence Gemini API limit is enforced at the node level.

import pytest

from gemini.nodes import _parse_stop_sequences


class TestParseStopSequences:
    """Tests for the stop sequence parser."""

    def test_empty_string_returns_none(self):
        assert _parse_stop_sequences("") is None

    def test_whitespace_only_returns_none(self):
        assert _parse_stop_sequences("   \n\n  ") is None

    def test_single_sequence(self):
        assert _parse_stop_sequences("STOP") == ["STOP"]

    def test_multiple_sequences_newline_separated(self):
        result = _parse_stop_sequences("END\nSTOP\nDONE")
        assert result == ["END", "STOP", "DONE"]

    def test_strips_whitespace_from_entries(self):
        result = _parse_stop_sequences("  END  \n  STOP  ")
        assert result == ["END", "STOP"]

    def test_skips_blank_lines(self):
        result = _parse_stop_sequences("END\n\n\nSTOP\n\n")
        assert result == ["END", "STOP"]

    def test_exactly_five_sequences_allowed(self):
        text = "\n".join(["SEQ1", "SEQ2", "SEQ3", "SEQ4", "SEQ5"])
        result = _parse_stop_sequences(text)
        assert result == ["SEQ1", "SEQ2", "SEQ3", "SEQ4", "SEQ5"]

    def test_more_than_five_truncated_to_five(self):
        text = "\n".join([f"SEQ{i}" for i in range(1, 9)])
        result = _parse_stop_sequences(text)
        assert len(result) == 5
        assert result == ["SEQ1", "SEQ2", "SEQ3", "SEQ4", "SEQ5"]

    def test_more_than_five_logs_warning(self, capsys):
        text = "\n".join([f"SEQ{i}" for i in range(1, 9)])
        _parse_stop_sequences(text)
        captured = capsys.readouterr()
        assert "5" in captured.out
        assert "8" in captured.out or "truncat" in captured.out.lower()
