# ABOUTME: WaveSpeed AI provider package for ComfyUI V3.
# ABOUTME: Exports flat NODES list of all 45 WaveSpeed node classes for ERPKExtension.

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
from .qwen_image_edit_lora import QwenImageEditLoraNode
from .qwen_image_edit_plus_lora import QwenImageEditPlusLoraNode
from .qwen_image_layered import QwenImageLayeredNode
from .qwen_image_2_0_text_to_image import QwenImage20TextToImageNode
from .qwen_image_2_0_edit import QwenImage20EditNode
from .seedream_v5_lite import SeedreamV5LiteNode
from .seedream_v5_lite_edit import SeedreamV5LiteEditNode
from .seedream_v5_lite_sequential import SeedreamV5LiteSequentialNode
from .seedream_v5_lite_edit_sequential import SeedreamV5LiteEditSequentialNode
from .qwen_image_max import QwenImageMaxNode
from .qwen_image_max_edit import QwenImageMaxEditNode
from .jibmix_qwen_image import JibMixQwenImageNode
from .dreamina_text_to_image import DreaminaTextToImageNode
from .dreamina_edit import DreaminaEditNode
from .seedance_2_0_text_to_video import Seedance20TextToVideoNode
from .seedance_2_0_image_to_video import Seedance20ImageToVideoNode
from .wan_2_7_text_to_video import Wan27TextToVideoNode
from .wan_2_7_image_to_video import Wan27ImageToVideoNode
from .wan_2_7_video_extend import Wan27VideoExtendNode
from .wavespeed_veo_3_1_text_to_video import WaveSpeedVeo31TextToVideoNode
from .wavespeed_veo_3_1_image_to_video import WaveSpeedVeo31ImageToVideoNode
from .kling_v3_image_to_video import KlingV3ImageToVideoNode
from .kling_o3_text_to_video import KlingO3TextToVideoNode
from .kling_o3_image_to_video import KlingO3ImageToVideoNode
from .ltx_2_pro_text_to_video import Ltx2ProTextToVideoNode
from .ltx_2_pro_image_to_video import Ltx2ProImageToVideoNode
from .ltx_2_3_text_to_video import Ltx23TextToVideoNode
from .ltx_2_3_image_to_video import Ltx23ImageToVideoNode

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
    QwenImageEditLoraNode,
    QwenImageEditPlusLoraNode,
    QwenImageLayeredNode,
    QwenImage20TextToImageNode,
    QwenImage20EditNode,
    SeedreamV5LiteNode,
    SeedreamV5LiteEditNode,
    SeedreamV5LiteSequentialNode,
    SeedreamV5LiteEditSequentialNode,
    QwenImageMaxNode,
    QwenImageMaxEditNode,
    JibMixQwenImageNode,
    DreaminaTextToImageNode,
    DreaminaEditNode,
    Seedance20TextToVideoNode,
    Seedance20ImageToVideoNode,
    Wan27TextToVideoNode,
    Wan27ImageToVideoNode,
    Wan27VideoExtendNode,
    WaveSpeedVeo31TextToVideoNode,
    WaveSpeedVeo31ImageToVideoNode,
    KlingV3ImageToVideoNode,
    KlingO3TextToVideoNode,
    KlingO3ImageToVideoNode,
    Ltx2ProTextToVideoNode,
    Ltx2ProImageToVideoNode,
    Ltx23TextToVideoNode,
    Ltx23ImageToVideoNode,
]

__all__ = ["NODES"]
