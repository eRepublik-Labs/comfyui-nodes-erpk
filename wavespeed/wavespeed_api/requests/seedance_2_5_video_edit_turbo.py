# ABOUTME: Seedance 2.5 Turbo video-edit request for WaveSpeed AI.
# ABOUTME: Routes to the -turbo endpoint with identical payload.

from .seedance_2_5_video_edit import Seedance25VideoEdit


class Seedance25VideoEditTurbo(Seedance25VideoEdit):
    """Seedance 2.5 Turbo, same parameters, turbo endpoint."""

    def get_api_path(self):
        return "/api/v3/bytedance/seedance-2.5/video-edit-turbo"
