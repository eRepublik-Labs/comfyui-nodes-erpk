# ABOUTME: Kling Elements creation node for WaveSpeed AI.
# ABOUTME: Generates an element ID for use in Pro variants' element_list field.

import json
from comfy_api.latest import IO


class KlingElementsNode(IO.ComfyNode):
    """
    Kling Elements Creation Node

    Creates a Kling element (consistent character/style/scene anchor)
    and returns its element ID. Reference the returned ID from Pro
    variant Kling i2v/t2v generation nodes via their `element_list`
    JSON-array input for visual continuity across scenes.

    Image inputs accept either a ComfyUI IMAGE tensor (sent as a base64
    data URI) or a URL string. When both are provided for the same
    field, the IMAGE input takes precedence.
    """

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="KlingElementsNode",
            display_name="Kling Elements",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.String.Input("name", default="",
                                tooltip="Element name (max 20 characters)"),
                IO.String.Input("description", multiline=True, default="",
                                tooltip="Element description (max 100 characters)"),
                IO.Image.Input("image", optional=True,
                               tooltip="Front reference image as a ComfyUI IMAGE tensor. Preferred — takes precedence over `image_url` when connected. Source should be ≥300px and ≤10MB after encoding."),
                IO.String.Input("image_url", optional=True, default="",
                                tooltip="Front reference image URL. Fallback when the IMAGE input is not connected."),
                IO.Image.Input("element_refer_images", optional=True,
                               tooltip="Batched IMAGE tensor of 1-3 additional reference images. Preferred over `element_refer_url_list` when connected."),
                IO.String.Input("element_refer_url_list", optional=True, multiline=True, default="",
                                tooltip="JSON array of 1-3 additional reference image URLs. Used only when `element_refer_images` is not connected."),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.String.Input("voice_id", optional=True, default="",
                                tooltip="Bind an existing voice/tone to this element"),
                IO.String.Input("tag_list", optional=True, multiline=True, default="",
                                tooltip="JSON array of tags for organizing the element"),
            ],
            outputs=[
                IO.String.Output("element_id"),
            ],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return float("NaN")

    @classmethod
    def _parse_json_array(cls, raw, field_name):
        if raw is None or raw == "":
            return None
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"{field_name} must be a valid JSON array: {e}") from e
        if not isinstance(value, list):
            raise ValueError(f"{field_name} must be a JSON array, got {type(value).__name__}")
        return value

    @classmethod
    def execute(cls, name="", description="", image=None, image_url="",
                element_refer_images=None, element_refer_url_list="",
                client=None, voice_id="", tag_list="", **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import image_to_data_uri, images_to_data_uris
        from .wavespeed_api.requests.kling_elements import KlingElements

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        if name is None or name == "":
            raise ValueError("Element name is required")
        if description is None or description == "":
            raise ValueError("Element description is required")

        image_value = image_to_data_uri(image) if image is not None else (image_url or None)
        if not image_value:
            raise ValueError("Front reference image is required (IMAGE input or image_url)")

        if element_refer_images is not None:
            refer_list = images_to_data_uris(element_refer_images, max_count=3)
        else:
            refer_list = cls._parse_json_array(element_refer_url_list, "element_refer_url_list")
        if refer_list is None or len(refer_list) == 0:
            raise ValueError("element_refer_list must contain 1-3 image URLs or tensors")

        tag_list_value = cls._parse_json_array(tag_list, "tag_list")

        request = KlingElements(
            name=name,
            description=description,
            image=image_value,
            element_refer_list=refer_list,
            voice_id=voice_id if voice_id else None,
            tag_list=tag_list_value,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = waveSpeedClient.send_request(request, True, polling_interval=5, timeout=300)

        element_id = response.get("id") or response.get("data", {}).get("id", "")
        if not element_id:
            outputs = response.get("outputs", [])
            if outputs:
                element_id = outputs[0]
        if not element_id:
            raise ValueError(f"Could not extract element_id from response: {response}")
        return IO.NodeOutput(element_id)
