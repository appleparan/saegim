"""Model adapters for VLM/OCR response parsing."""

from typing import Any


def extract_content(result: dict[str, Any]) -> str:
    """Extract text content from OpenAI-compatible response.

    Args:
        result: Raw API response dict.

    Returns:
        Text content string, or empty string if not available.
    """
    choices = result.get('choices', [])
    if not choices:
        return ''
    message = choices[0].get('message', {})
    return message.get('content', '')
