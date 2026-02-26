# ABOUTME: WaveSpeed AI provider package for ComfyUI V3.
# ABOUTME: Exports flat NODES list of all 18 WaveSpeed node classes for ERPKExtension.

from .nodes import WaveSpeedAIAPIClient, PreviewVideo, SaveAudio, UploadImage
from .seedream_v4 import SeedreamV4Node
from .seedream_v4_edit import SeedreamV4EditNode
from .seedream_v4_sequential import SeedreamV4SequentialNode
from .seedream_v4_edit_sequential import SeedreamV4EditSequentialNode
from .seedream_v4_5 import SeedreamV4_5Node
from .seedream_v4_5_edit import SeedreamV4_5EditNode
from .seedream_v4_5_sequential import SeedreamV4_5SequentialNode
from .seedream_v4_5_edit_sequential import SeedreamV4_5EditSequentialNode
from .qwen_image_text_to_image import QwenImageTextToImageNode
from .qwen_image_edit import QwenImageEditNode
from .qwen_image_edit_plus import QwenImageEditPlusNode
from .qwen_image_multiple_angles import QwenImageMultipleAnglesNode
from .qwen_image_lora import QwenImageLoraNode
from .qwen_image_layered import QwenImageLayeredNode

NODES = [
    WaveSpeedAIAPIClient,
    PreviewVideo,
    SaveAudio,
    UploadImage,
    SeedreamV4Node,
    SeedreamV4EditNode,
    SeedreamV4SequentialNode,
    SeedreamV4EditSequentialNode,
    SeedreamV4_5Node,
    SeedreamV4_5EditNode,
    SeedreamV4_5SequentialNode,
    SeedreamV4_5EditSequentialNode,
    QwenImageTextToImageNode,
    QwenImageEditNode,
    QwenImageEditPlusNode,
    QwenImageMultipleAnglesNode,
    QwenImageLoraNode,
    QwenImageLayeredNode,
]

__all__ = ["NODES"]
