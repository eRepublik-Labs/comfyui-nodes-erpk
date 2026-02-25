# ABOUTME: Package init for WaveSpeed API integration module.
# ABOUTME: Exports WaveSpeedClient; heavy utilities are lazy-imported by callers.

"""
WaveSpeed API module for ComfyUI integration
"""

from .client import WaveSpeedClient

__all__ = [
    'WaveSpeedClient',
]
