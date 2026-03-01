"""Engine factory for building OCR engines from configuration.

Dispatches on the 'engine_type' key to create the appropriate engine.
"""

import logging
from typing import Any

from saegim.services.engines.base import BaseOCREngine

logger = logging.getLogger(__name__)


def build_engine(ocr_config: dict[str, Any]) -> BaseOCREngine:
    """Build an OCR engine from configuration.

    Args:
        ocr_config: OCR configuration dict with 'engine_type' key.

    Returns:
        BaseOCREngine instance for the specified engine type.

    Raises:
        ValueError: If engine_type is missing or unknown.
    """
    engine_type = ocr_config.get('engine_type', '')

    if engine_type == 'pdfminer':
        return _build_pdfminer()

    if engine_type == 'commercial_api':
        return _build_commercial_api(ocr_config.get('commercial_api', {}))

    if engine_type == 'vllm':
        return _build_vllm(ocr_config.get('vllm', {}))

    if engine_type == 'split_pipeline':
        return _build_split_pipeline(ocr_config.get('split_pipeline', {}))

    valid = "'commercial_api', 'vllm', 'split_pipeline', 'pdfminer'"
    msg = f"Unknown engine_type: '{engine_type}'. Use {valid}."
    raise ValueError(msg)


def _build_pdfminer() -> BaseOCREngine:
    """Build a pdfminer fallback engine.

    Returns:
        PdfminerEngine instance.
    """
    from saegim.services.engines.pdfminer_engine import PdfminerEngine

    return PdfminerEngine()


def _build_commercial_api(config: dict[str, Any]) -> BaseOCREngine:
    """Build a commercial API engine.

    Args:
        config: Commercial API config with 'provider', 'api_key', etc.

    Returns:
        CommercialApiEngine instance.
    """
    from saegim.services.engines.commercial_api_engine import CommercialApiEngine

    provider = config.get('provider', '')
    return CommercialApiEngine(provider=provider, config=config)


def _build_vllm(config: dict[str, Any]) -> BaseOCREngine:
    """Build a vLLM server engine.

    Args:
        config: vLLM config with 'host', 'port', 'model'.

    Returns:
        VllmEngine instance.
    """
    from saegim.services.engines.vllm_engine import VllmEngine

    host = config.get('host', 'localhost')
    port = config.get('port', 8000)
    model = config.get('model', 'datalab-to/chandra')
    return VllmEngine(host=host, port=port, model=model)


def _build_split_pipeline(config: dict[str, Any]) -> BaseOCREngine:
    """Build a split pipeline engine (Docling layout + text OCR).

    Args:
        config: Split pipeline config with 'docling_model_name', 'ocr_provider', etc.

    Returns:
        SplitPipelineEngine instance.
    """
    from saegim.services.engines.split_pipeline_engine import SplitPipelineEngine

    docling_model_name = config.get('docling_model_name', 'ibm-granite/granite-docling-258M')
    ocr_provider = config.get('ocr_provider', '')
    ocr_config = {
        k.removeprefix('ocr_'): v
        for k, v in config.items()
        if k.startswith('ocr_') and k != 'ocr_provider'
    }
    return SplitPipelineEngine(
        docling_model_name=docling_model_name,
        ocr_provider=ocr_provider,
        ocr_config=ocr_config,
    )
