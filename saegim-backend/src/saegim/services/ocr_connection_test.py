"""OCR provider connection test service.

Tests connectivity to PP-StructureV3, Gemini API, or vLLM server.
Supports the 2-stage pipeline: layout_provider + ocr_provider.
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GEMINI_API_BASE = 'https://generativelanguage.googleapis.com/v1beta'


def check_ppstructure_connection(config: dict[str, Any]) -> tuple[bool, str]:
    """Test PP-StructureV3 server connectivity.

    Args:
        config: PP-StructureV3 config dict with 'host' and 'port'.

    Returns:
        Tuple of (success, message).
    """
    host = config.get('host', 'localhost')
    port = config.get('port', 18811)
    url = f'http://{host}:{port}/api/v1/health'

    try:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.get(url)
            response.raise_for_status()
            return True, f'Connected to PP-StructureV3 at {host}:{port}'
    except httpx.RequestError as exc:
        return False, f'Cannot connect to PP-StructureV3 at {host}:{port}: {exc}'
    except httpx.HTTPStatusError as exc:
        return False, f'PP-StructureV3 error: {exc.response.status_code}'


def check_gemini_connection(config: dict[str, Any]) -> tuple[bool, str]:
    """Test Gemini API connectivity by listing models.

    Args:
        config: Gemini config dict with 'api_key' and optional 'model'.

    Returns:
        Tuple of (success, message).
    """
    api_key = config.get('api_key', '')
    if not api_key:
        return False, 'API key is required'

    model = config.get('model', 'gemini-2.0-flash')
    url = f'{_GEMINI_API_BASE}/models/{model}?key={api_key}'

    try:
        with httpx.Client(timeout=httpx.Timeout(15.0)) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            model_name = data.get('displayName', model)
            return True, f'Connected to Gemini ({model_name})'
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 403:
            return False, 'Invalid API key or insufficient permissions'
        if exc.response.status_code == 404:
            return False, f'Model not found: {model}'
        return False, f'Gemini API error: {exc.response.status_code}'
    except httpx.RequestError as exc:
        return False, f'Connection failed: {exc}'


def check_vllm_connection(config: dict[str, Any]) -> tuple[bool, str]:
    """Test vLLM server connectivity by listing models.

    Args:
        config: vLLM config dict with 'host', 'port', and optional 'model'.

    Returns:
        Tuple of (success, message).
    """
    host = config.get('host', 'localhost')
    port = config.get('port', 8000)
    url = f'http://{host}:{port}/v1/models'

    try:
        with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            models = data.get('data', [])
            if models:
                model_ids = [m.get('id', '?') for m in models[:3]]
                return True, f'Connected to vLLM ({", ".join(model_ids)})'
            return True, f'Connected to vLLM at {host}:{port}'
    except httpx.RequestError as exc:
        return False, f'Cannot connect to vLLM at {host}:{port}: {exc}'
    except httpx.HTTPStatusError as exc:
        return False, f'vLLM error: {exc.response.status_code}'


def check_ocr_connection(ocr_config: dict[str, Any]) -> tuple[bool, str]:
    """Test OCR pipeline connection based on 2-stage configuration.

    Tests both layout_provider and ocr_provider connections.

    Args:
        ocr_config: OCR config dict with 'layout_provider' and 'ocr_provider'.

    Returns:
        Tuple of (success, message).
    """
    layout_provider = ocr_config.get('layout_provider', '')

    if layout_provider == 'pymupdf':
        return True, 'PyMuPDF does not require a connection test'

    if layout_provider == 'ppstructure':
        return _check_ppstructure_pipeline(ocr_config)

    return False, f'Unknown layout provider: {layout_provider}'


def _check_ppstructure_pipeline(
    ocr_config: dict[str, Any],
) -> tuple[bool, str]:
    """Test PP-StructureV3 pipeline connections.

    Tests PP-StructureV3 server and the selected OCR provider.

    Args:
        ocr_config: Full OCR config dict.

    Returns:
        Tuple of (success, message).
    """
    # Test PP-StructureV3 connection
    pp_config = ocr_config.get('ppstructure', {})
    pp_ok, pp_msg = check_ppstructure_connection(pp_config)
    if not pp_ok:
        return False, pp_msg

    # Test OCR provider connection
    ocr_provider = ocr_config.get('ocr_provider', '')

    if ocr_provider == 'gemini':
        gemini_config = ocr_config.get('gemini', {})
        ocr_ok, ocr_msg = check_gemini_connection(gemini_config)
        if not ocr_ok:
            return False, ocr_msg
        return True, f'{pp_msg} | {ocr_msg}'

    if ocr_provider == 'olmocr':
        vllm_config = ocr_config.get('vllm', {})
        ocr_ok, ocr_msg = check_vllm_connection(vllm_config)
        if not ocr_ok:
            return False, ocr_msg
        return True, f'{pp_msg} | {ocr_msg}'

    if ocr_provider == 'ppocr':
        return True, f'{pp_msg} (PP-OCR built-in)'

    return False, f'Unknown OCR provider: {ocr_provider}'
