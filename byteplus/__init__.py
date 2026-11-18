# ABOUTME: BytePlus ModelArk provider V3 node registration for ERPKExtension aggregation.
# ABOUTME: Exports the NODES list consumed by the top-level __init__.py provider loop.

from .nodes import BytePlusAPIClient, BytePlusSeedreamTextToImage, BytePlusSeedreamImageEdit
from .video_nodes import (
    BytePlusSeedanceTextToVideo, BytePlusSeedanceImageToVideo, BytePlusSeedanceReferenceToVideo,
)

NODES = [
    BytePlusAPIClient,
    BytePlusSeedanceTextToVideo,
    BytePlusSeedanceImageToVideo,
    BytePlusSeedanceReferenceToVideo,
    BytePlusSeedreamTextToImage,
    BytePlusSeedreamImageEdit,
]

__all__ = ["NODES"]
