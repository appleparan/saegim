"""Image processing utilities shared across services."""

import io

from PIL import Image


def crop_region(
    image: Image.Image,
    bbox: tuple[float, float, float, float],
) -> bytes:
    """Crop a region from an image and return as PNG bytes.

    Coordinates are clamped to image bounds before cropping.

    Args:
        image: Full page PIL Image.
        bbox: Bounding box as (x1, y1, x2, y2) in pixels.

    Returns:
        Cropped image as PNG bytes, empty bytes if region has zero area.
    """
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(x1, image.width))
    y1 = max(0, min(y1, image.height))
    x2 = max(0, min(x2, image.width))
    y2 = max(0, min(y2, image.height))

    ix1, iy1, ix2, iy2 = int(x1), int(y1), int(x2), int(y2)
    if ix2 <= ix1 or iy2 <= iy1:
        return b''

    cropped = image.crop((ix1, iy1, ix2, iy2))
    buf = io.BytesIO()
    cropped.save(buf, format='PNG')
    return buf.getvalue()
