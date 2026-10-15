# ABOUTME: Qwen Image Multiple Angles node on WaveSpeed's 96-pose camera system.
# ABOUTME: Re-renders a subject from a chosen azimuth, elevation and framing distance.

from comfy_api.latest import IO


class QwenImageMultipleAngles96Node(IO.ComfyNode):
    """
    Qwen Image Multiple Angles (96 poses) Node

    Re-renders the subject of 1 to 3 reference images from one of 96 camera
    poses: 8 azimuths around the subject, 4 elevations and 3 framing
    distances. Each dropdown offers only the poses the model renders.
    """

    AZIMUTHS = {
        "front (0°)": 0,
        "front-right (45°)": 45,
        "right side (90°)": 90,
        "back-right (135°)": 135,
        "back (180°)": 180,
        "back-left (225°)": 225,
        "left side (270°)": 270,
        "front-left (315°)": 315,
    }
    ELEVATIONS = {
        "low angle (-30°)": -30,
        "eye level (0°)": 0,
        "elevated (30°)": 30,
        "high angle (60°)": 60,
    }
    DISTANCES = {
        "close-up": 0,
        "medium": 1,
        "wide": 2,
    }
    MAX_IMAGES = 3

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="QwenImageMultipleAngles96Node",
            display_name="Qwen Image Multiple Angles (96 poses)",
            category="ERPK/WaveSpeedAI",
            inputs=[
                IO.Image.Input("reference_images", optional=True,
                               tooltip="Reference images as a ComfyUI IMAGE batch, up to 3. Each slice is one image. "
                                       "Takes precedence over `reference_images_url`. Sent inline as base64, no upload."),
                IO.String.Input("reference_images_url", optional=True, default="",
                                tooltip="Reference image URLs, up to 3, separated by commas or newlines. "
                                        "Ignored when `reference_images` is connected."),
                IO.String.Input("prompt", optional=True, multiline=True, default="",
                                tooltip="Optional guidance appended to the camera-angle prompt"),
                IO.Custom("WAVESPEED_AI_API_CLIENT").Input("client", optional=True,
                    tooltip="WaveSpeed API client (optional if API key is configured in Settings)"),
                IO.Combo.Input("azimuth", optional=True, options=list(cls.AZIMUTHS), default="front (0°)",
                               tooltip="Camera position around the subject; 0° is the front view"),
                IO.Combo.Input("elevation", optional=True, options=list(cls.ELEVATIONS), default="eye level (0°)",
                               tooltip="Camera height relative to the subject"),
                IO.Combo.Input("framing", optional=True, options=list(cls.DISTANCES), default="medium",
                               tooltip="Camera distance: close-up, medium or wide shot"),
                IO.Int.Input("seed", optional=True, default=-1, min=-1, max=2147483647,
                             control_after_generate="randomize",
                             tooltip="Generation seed, sent to the API. A fixed seed reproduces the same result and "
                                     "lets ComfyUI reuse the cached output; -1 generates a new one each queue."),
                IO.Combo.Input("output_format", optional=True, options=["jpeg", "png", "webp"], default="jpeg",
                               tooltip="Output image format. $0.025 per image."),
            ],
            outputs=[
                IO.Image.Output("image"),
            ],
            not_idempotent=True,
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        seed = kwargs.get("seed", -1)
        return float("NaN") if seed == -1 else seed

    @classmethod
    async def execute(cls, reference_images=None, reference_images_url="", prompt="", client=None,
                      azimuth="front (0°)", elevation="eye level (0°)", framing="medium", seed=-1,
                      output_format="jpeg", **kwargs):
        from .wavespeed_api.client import WaveSpeedClient
        from .wavespeed_api.utils import imageurl2tensor, input_image_list
        from .wavespeed_api.requests.qwen_image_multiple_angles_96 import QwenImageMultipleAngles96

        if client is None:
            from .nodes import WaveSpeedAIAPIClient
            client = WaveSpeedAIAPIClient.execute()[0]

        images_param = input_image_list(reference_images, reference_images_url, cls.MAX_IMAGES,
                                        "Qwen Image Multiple Angles (96 poses)")
        if not images_param:
            raise ValueError("Connect reference_images or enter at least one image URL")

        request = QwenImageMultipleAngles96(
            images=images_param,
            horizontal_angle=cls.AZIMUTHS[azimuth],
            vertical_angle=cls.ELEVATIONS[elevation],
            distance=cls.DISTANCES[framing],
            prompt=prompt or None,
            seed=seed,
            output_format=output_format,
        )

        waveSpeedClient = WaveSpeedClient(client["api_key"])
        response = await waveSpeedClient.send_request(request, True, 1)

        image_urls = response.get("outputs", [])
        if not image_urls:
            raise ValueError("No image URLs in the generated result")

        images = imageurl2tensor(image_urls)
        return IO.NodeOutput(images)
