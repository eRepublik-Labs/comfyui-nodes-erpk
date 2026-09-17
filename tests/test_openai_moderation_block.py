# ABOUTME: Tests that an OpenAI safety refusal is recognised and reported with its stage and categories.
# ABOUTME: The images API returns code `moderation_blocked`, not the `content_policy_violation` once assumed.

"""
A refused image generation comes back as HTTP 400 with this body, captured
live from /images/generations on 2026-09-17:

    {"error": {"message": "Your request was rejected by the safety system...",
               "type": "image_generation_user_error",
               "code": "moderation_blocked",
               "moderation_details": {"moderation_stage": "input",
                                      "categories": ["other"]}}}

The client previously branched on `content_policy_violation`, so the graceful
blocked path never ran for images and the caller saw a raw APIError instead.
`moderation_stage` is the useful half: it says whether the prompt was refused
or the finished image was, which decides whether rewording can help.
"""

import sys
from unittest.mock import MagicMock

import pytest

import openai as _local_openai
if not hasattr(_local_openai, "APIError"):
    _local_openai.APIError = type("APIError", (Exception,), {})

from openai.openai_api.client import OpenAIClient  # noqa: E402


def _refusal(code="moderation_blocked", stage="input", categories=("other",),
             message="Your request was rejected by the safety system."):
    """Build an APIError shaped like a real moderation refusal."""
    error = _local_openai.APIError(message)
    error.code = code
    payload = {"message": message, "type": "image_generation_user_error", "code": code}
    if stage is not None or categories is not None:
        payload["moderation_details"] = {}
        if stage is not None:
            payload["moderation_details"]["moderation_stage"] = stage
        if categories is not None:
            payload["moderation_details"]["categories"] = list(categories)
    error.body = {"error": payload}
    return error


class TestRecognisingARefusal:

    def test_moderation_blocked_is_recognised(self):
        assert OpenAIClient._moderation_block(_refusal()) is not None

    def test_content_policy_violation_is_still_recognised(self):
        # Kept because the chat path has long branched on it; dropping it would
        # silently turn a handled refusal there into a raised error.
        assert OpenAIClient._moderation_block(_refusal(code="content_policy_violation")) is not None

    def test_an_unrelated_error_is_not_a_refusal(self):
        assert OpenAIClient._moderation_block(_refusal(code="rate_limit_exceeded")) is None

    def test_an_error_without_a_code_is_not_a_refusal(self):
        assert OpenAIClient._moderation_block(Exception("boom")) is None


class TestRefusalDetail:

    def test_stage_and_categories_are_extracted(self):
        block = OpenAIClient._moderation_block(_refusal(stage="output", categories=["violence"]))

        assert block["stage"] == "output"
        assert block["categories"] == ["violence"]

    def test_missing_details_do_not_raise(self):
        # The guide calls moderation_details optional.
        block = OpenAIClient._moderation_block(_refusal(stage=None, categories=None))

        assert block["stage"] is None
        assert block["categories"] == []

    def test_a_body_that_is_not_a_dict_does_not_raise(self):
        error = _refusal()
        error.body = "<html>gateway error</html>"

        assert OpenAIClient._moderation_block(error)["categories"] == []

    def test_the_two_stages_give_different_advice(self):
        # "input" means the prompt was refused, so rewording can help. "output"
        # means the prompt passed and the render was refused, where it may not.
        # The message must say which, in words the node's user can act on.
        on_input = OpenAIClient._moderation_message(
            OpenAIClient._moderation_block(_refusal(stage="input", categories=["other"]))
        )
        on_output = OpenAIClient._moderation_message(
            OpenAIClient._moderation_block(_refusal(stage="output", categories=["other"]))
        )

        assert "prompt was refused" in on_input
        assert "Try rewording" in on_input
        assert "generated image was refused" in on_output
        assert "may not help" in on_output
        assert on_input != on_output
        assert "other" in on_input

    def test_message_survives_absent_detail(self):
        message = OpenAIClient._moderation_message(
            OpenAIClient._moderation_block(_refusal(stage=None, categories=None))
        )

        assert message
        assert "None" not in message


class TestImagePathsReturnBlockedRatherThanRaising:
    """Each image path must take the graceful branch, not re-raise."""

    def _client_raising(self, error):
        client = OpenAIClient.__new__(OpenAIClient)
        sdk = MagicMock()
        sdk.images.generate.side_effect = error
        sdk.images.edit.side_effect = error
        sdk.responses.create.side_effect = error
        client.client = sdk
        client.system_instruction = None
        return client

    def test_generate_image_reports_blocked(self):
        client = self._client_raising(_refusal())

        result = client._generate_image_sync(prompt="x", model="gpt-image-2")

        assert result["blocked"] is True
        assert result["images"] == []
        assert result["moderation_stage"] == "input"

    def test_edit_image_reports_blocked(self):
        client = self._client_raising(_refusal(stage="output"))

        result = client._edit_image_sync(image_data=b"x", prompt="x", model="gpt-image-2")

        assert result["blocked"] is True
        assert result["moderation_stage"] == "output"

    def test_responses_path_reports_blocked(self):
        client = self._client_raising(_refusal())

        result = client._generate_image_via_responses_sync(prompt="x")

        assert result["blocked"] is True
        assert result["moderation_stage"] == "input"

    def test_a_non_moderation_error_still_raises(self):
        client = self._client_raising(_refusal(code="server_error"))

        with pytest.raises(Exception):
            client._generate_image_sync(prompt="x", model="gpt-image-2")
