"""Adapter resolution based on model name."""

from saegim.services.adapters.base import ModelAdapter
from saegim.services.adapters.chandra import ChandraAdapter
from saegim.services.adapters.lightonocr import LightOnOcrAdapter


def resolve_adapter(model_name: str) -> ModelAdapter:
    """Resolve the appropriate adapter for a model.

    Inspects the model name to determine which adapter to use:
    - ``lighton`` in name → LightOnOcrAdapter (prompt-free, 0-1000 coords)
    - Everything else → ChandraAdapter (STRUCTURED_OCR_PROMPT-based)

    Args:
        model_name: Full model name string.

    Returns:
        ModelAdapter instance.
    """
    lower = model_name.lower()
    if 'lightonocr' in lower or 'lighton' in lower:
        return LightOnOcrAdapter()
    return ChandraAdapter()
