"""Base protocol for model adapters."""

from typing import Any, Protocol

from saegim.services.docir import PageIR


class ModelAdapter(Protocol):
    """Protocol for model-specific adapters.

    Adapters handle prompt construction and response parsing
    for different VLM/OCR models.
    """

    def build_messages(
        self,
        image_b64: str,
        mime_type: str,
        page_width: int,
        page_height: int,
    ) -> list[dict[str, Any]]:
        """Build API messages for the model.

        Args:
            image_b64: Base64-encoded image data.
            mime_type: Image MIME type.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            List of message dicts for the API.
        """
        ...

    def parse_response(
        self,
        result: dict[str, Any],
        page_width: int,
        page_height: int,
    ) -> PageIR:
        """Parse API response into PageIR.

        Args:
            result: Raw API response dict.
            page_width: Image width in pixels.
            page_height: Image height in pixels.

        Returns:
            Parsed PageIR.
        """
        ...
