"""OCR provider connection test service.

Individual connection checks for Gemini API and vLLM server.
Used by engine classes for their test_connection() implementations.
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GEMINI_API_BASE = 'https://generativelanguage.googleapis.com/v1beta'


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

    model = config.get('model', 'gemini-3-flash-preview')
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
