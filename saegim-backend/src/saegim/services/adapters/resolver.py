"""Adapter resolution based on model name."""

from saegim.services.adapters.base import ModelAdapter
from saegim.services.adapters.chandra import ChandraAdapter


def resolve_adapter(model_name: str) -> ModelAdapter:
    """Resolve the appropriate adapter for a model.

    Currently all models use ChandraAdapter (STRUCTURED_OCR_PROMPT-based).
    Future adapters (e.g. LightOnOCR) will be resolved by model name pattern.

    Args:
        model_name: Full model name string.

    Returns:
        ModelAdapter instance.
    """
    _ = model_name  # reserved for future pattern matching
    return ChandraAdapter()
