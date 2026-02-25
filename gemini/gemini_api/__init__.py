# ABOUTME: API integration layer for Google Gemini.
# ABOUTME: Exports client class; utils are imported lazily by nodes that need them.

from .client import GeminiClient

__all__ = ['GeminiClient']
