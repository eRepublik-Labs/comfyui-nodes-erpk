# ABOUTME: Tests the max_tokens widget on the Gemini text nodes and how a reply that hits it is reported.
# ABOUTME: A cut-off reply raises, and a reply with no text reports why instead of crashing.

"""
Measured 2026-11-03 through the real nodes (gemini_study): gemini-4-argon at
max_tokens=256 returned '' and gemini-3.8-flash returned ' we use $N = 4 p_',
both with finish_reason MAX_TOKENS, and both printed "Text generated
successfully". Thinking counts toward max_output_tokens, so a low cap can end
the reply before any text. At a 32-token cap response.text was None.
"""

import asyncio
from types import SimpleNamespace

import pytest
from google.genai import types

from gemini.gemini_api.client import GeminiClient
from gemini.nodes import GeminiChat, GeminiDetect, GeminiTextGeneration, GeminiVision

CUT_OFF_TEXT = " we use $N = 4 p_"


class TestMaxTokensCeiling:
    """Verify max_tokens ceiling is 65536 in define_schema."""

    @pytest.mark.parametrize("node_cls", [GeminiTextGeneration, GeminiChat, GeminiVision])
    def test_max_tokens_ceiling_is_65536(self, node_cls):
        schema = node_cls.define_schema()
        max_tokens_input = [i for i in schema.inputs if i.id == "max_tokens"][0]
        assert max_tokens_input.max == 65536

    @pytest.mark.parametrize("node_cls", [GeminiTextGeneration, GeminiChat, GeminiVision])
    def test_max_tokens_default_is_8192(self, node_cls):
        """Default stays at 8192 — we only raise the ceiling, not the default."""
        schema = node_cls.define_schema()
        max_tokens_input = [i for i in schema.inputs if i.id == "max_tokens"][0]
        assert max_tokens_input.default == 8192


def _cut_off_message(max_tokens):
    return (f"Gemini's reply was cut off at max_output_tokens={max_tokens} "
            "(thinking counts toward it); raise max_output_tokens")


def _response(text, finish_reason):
    content = None if text is None else types.Content(role="model", parts=[types.Part(text=text)])
    return types.GenerateContentResponse(candidates=[types.Candidate(
        content=content, finish_reason=finish_reason)])


def _client_answering(response):
    """A real GeminiClient whose SDK models.generate_content returns response."""
    client = GeminiClient(api_key="test-key")
    client.client = SimpleNamespace(models=SimpleNamespace(
        generate_content=lambda model, contents, config: response))
    return client


def _image():
    torch = pytest.importorskip("torch")
    return torch.zeros(1, 8, 8, 3)


class TestCutOffReplies:
    @pytest.mark.parametrize("text", [CUT_OFF_TEXT, None])
    def test_text_generation_raises(self, text):
        client = _client_answering(_response(text, types.FinishReason.MAX_TOKENS))
        with pytest.raises(ValueError) as error:
            asyncio.run(GeminiTextGeneration.execute(prompt="Prove it.", client=client,
                                                     max_tokens=256))
        assert _cut_off_message(256) in str(error.value)

    def test_vision_raises(self):
        client = _client_answering(_response(CUT_OFF_TEXT, types.FinishReason.MAX_TOKENS))
        with pytest.raises(ValueError) as error:
            asyncio.run(GeminiVision.execute(image=_image(), prompt="Describe it.",
                                             client=client, max_tokens=512))
        assert _cut_off_message(512) in str(error.value)

    def test_detect_names_the_cap_it_ran_under(self):
        # Detect has no max_tokens widget, so the client default applies.
        client = _client_answering(_response('[{"box_2d": [1, 2', types.FinishReason.MAX_TOKENS))
        with pytest.raises(ValueError) as error:
            asyncio.run(GeminiDetect.execute(image=_image(), objects="cat", client=client))
        assert _cut_off_message(8192) in str(error.value)

    def test_chat_raises(self):
        session = SimpleNamespace(send_message=lambda message, config: _response(
            CUT_OFF_TEXT, types.FinishReason.MAX_TOKENS))
        with pytest.raises(ValueError) as error:
            asyncio.run(GeminiChat.execute(prompt="Prove it.", client=GeminiClient(api_key="test-key"),
                                           chat_session=session, max_tokens=384))
        assert _cut_off_message(384) in str(error.value)

    def test_complete_reply_is_returned(self):
        client = _client_answering(_response("Done.", types.FinishReason.STOP))
        output = asyncio.run(GeminiTextGeneration.execute(prompt="Say done.", client=client))
        assert output.args == ("Done.",)


class TestRepliesWithNoText:
    def test_safety_emptied_candidate_is_reported_as_blocked(self):
        client = _client_answering(_response(None, types.FinishReason.SAFETY))
        result = client._generate_content_sync("Hi")
        assert (result["blocked"], result["text"], result["finish_reason"]) == (True, "", "SAFETY")

    def test_blocked_prompt_names_its_block_reason(self):
        response = types.GenerateContentResponse(
            candidates=None,
            prompt_feedback=types.GenerateContentResponsePromptFeedback(
                block_reason=types.BlockedReason.PROHIBITED_CONTENT))
        result = _client_answering(response)._generate_content_sync("Hi")
        assert (result["blocked"], result["finish_reason"]) == (True, "PROHIBITED_CONTENT")

    def test_text_generation_reports_the_block(self):
        client = _client_answering(_response(None, types.FinishReason.SAFETY))
        with pytest.raises(ValueError) as error:
            asyncio.run(GeminiTextGeneration.execute(prompt="Hi", client=client))
        assert "Response blocked by safety filters. Reason: SAFETY" in str(error.value)

    def test_chat_reports_the_finish_reason(self):
        session = SimpleNamespace(send_message=lambda message, config: _response(
            None, types.FinishReason.SAFETY))
        with pytest.raises(ValueError) as error:
            asyncio.run(GeminiChat.execute(prompt="Hi", client=GeminiClient(api_key="test-key"),
                                           chat_session=session))
        assert "Gemini returned no text. Reason: SAFETY" in str(error.value)
