# ABOUTME: Tests for extracting the text of a Claude Messages response.
# ABOUTME: Thinking-only models return a thinking block before the text block.

from types import SimpleNamespace

import pytest

from claude.claude_api.client import response_text


def _response(*blocks):
    return SimpleNamespace(content=list(blocks))


def _thinking(text="hmm"):
    return SimpleNamespace(type="thinking", thinking=text)


def _text(text):
    return SimpleNamespace(type="text", text=text)


def test_skips_leading_thinking_block():
    # Adaptive thinking on claude-opus-4-7 puts a ThinkingBlock at content[0];
    # reading .text on it raised AttributeError in production (2026-09-22).
    assert response_text(_response(_thinking(), _text("Paris"))) == "Paris"


def test_plain_text_response_unchanged():
    assert response_text(_response(_text("Paris"))) == "Paris"


def test_joins_multiple_text_blocks():
    assert response_text(_response(_text("Par"), _thinking(), _text("is"))) == "Paris"


def test_thinking_only_response_raises():
    with pytest.raises(ValueError, match="^Claude returned no text block$"):
        response_text(_response(_thinking()))


def test_empty_response_raises():
    with pytest.raises(ValueError, match="^Claude returned no text block$"):
        response_text(_response())
