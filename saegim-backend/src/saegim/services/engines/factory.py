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

    if engine_type == 'integrated_server':
        return _build_integrated_server(ocr_config.get('integrated_server', {}))

    if engine_type == 'split_pipeline':
        return _build_split_pipeline(ocr_config.get('split_pipeline', {}))

    if engine_type == 'docling':
        return _build_docling(ocr_config.get('docling', {}))

    valid = "'commercial_api', 'integrated_server', 'split_pipeline', 'pdfminer', 'docling'"
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


def _build_integrated_server(config: dict[str, Any]) -> BaseOCREngine:
    """Build an integrated server engine.

    Args:
        config: Integrated server config with 'host', 'port', 'model'.

    Returns:
        IntegratedServerEngine instance.
    """
    from saegim.services.engines.integrated_server_engine import IntegratedServerEngine

    host = config.get('host', 'localhost')
    port = config.get('port', 8000)
    model = config.get('model', 'datalab-to/chandra')
    return IntegratedServerEngine(host=host, port=port, model=model)


def _build_split_pipeline(config: dict[str, Any]) -> BaseOCREngine:
    """Build a split pipeline engine.

    Args:
        config: Split pipeline config with 'layout_server_url', 'ocr_provider', etc.

    Returns:
        SplitPipelineEngine instance.
    """
    from saegim.services.engines.split_pipeline_engine import SplitPipelineEngine

    layout_url = config.get('layout_server_url', 'http://localhost:18811')
    ocr_provider = config.get('ocr_provider', '')
    ocr_config = {
        k.removeprefix('ocr_'): v
        for k, v in config.items()
        if k.startswith('ocr_') and k != 'ocr_provider'
    }
    return SplitPipelineEngine(
        layout_server_url=layout_url,
        ocr_provider=ocr_provider,
        ocr_config=ocr_config,
    )


def _build_docling(config: dict[str, Any]) -> BaseOCREngine:
    """Build a Docling layout detection engine.

    Args:
        config: Docling config with optional 'model_name'.

    Returns:
        DoclingEngine instance.
    """
    from saegim.services.engines.docling_engine import DoclingEngine

    model_name = config.get('model_name', 'ibm-granite/granite-docling-258M')
    return DoclingEngine(model_name=model_name)
