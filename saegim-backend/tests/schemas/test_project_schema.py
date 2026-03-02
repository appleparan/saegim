"""Tests for multi-instance OCR engine schemas."""

import pytest
from pydantic import ValidationError

from saegim.schemas.project import (
    EngineInstance,
    EngineInstanceCreate,
    EngineInstanceUpdate,
    OcrConfigResponse,
    generate_engine_id,
    slugify,
)


class TestSlugify:
    def test_simple_name(self):
        assert slugify('Gemini Flash') == 'gemini-flash'

    def test_special_characters(self):
        assert slugify('vLLM (Server #1)') == 'vllm-server-1'

    def test_multiple_spaces_and_hyphens(self):
        assert slugify('my  engine--name') == 'my-engine-name'

    def test_empty_string(self):
        assert slugify('') == 'engine'

    def test_only_special_chars(self):
        assert slugify('!!!') == 'engine'

    def test_leading_trailing_whitespace(self):
        assert slugify('  hello  ') == 'hello'

    def test_unicode_stripped(self):
        assert slugify('엔진 abc') == 'abc'


class TestGenerateEngineId:
    def test_no_collision(self):
        result = generate_engine_id('Gemini Flash', set())
        assert result == 'gemini-flash'

    def test_collision_adds_suffix(self):
        result = generate_engine_id('Gemini Flash', {'gemini-flash'})
        assert result == 'gemini-flash-2'

    def test_multiple_collisions(self):
        existing = {'gemini-flash', 'gemini-flash-2', 'gemini-flash-3'}
        result = generate_engine_id('Gemini Flash', existing)
        assert result == 'gemini-flash-4'


class TestEngineInstance:
    def test_valid_commercial_api(self):
        instance = EngineInstance(
            engine_type='commercial_api',
            name='Gemini Flash',
            config={
                'provider': 'gemini',
                'api_key': 'test-key',
                'model': 'gemini-3-flash-preview',
            },
        )
        assert instance.engine_type == 'commercial_api'
        assert instance.name == 'Gemini Flash'

    def test_valid_vllm(self):
        instance = EngineInstance(
            engine_type='vllm',
            name='vLLM Chandra',
            config={'host': 'gpu-server', 'port': 8000, 'model': 'datalab-to/chandra'},
        )
        assert instance.engine_type == 'vllm'

    def test_valid_split_pipeline(self):
        instance = EngineInstance(
            engine_type='split_pipeline',
            name='Docling + Gemini',
            config={
                'docling_model_name': 'ibm-granite/granite-docling-258M',
                'ocr_provider': 'gemini',
                'ocr_api_key': 'key',
            },
        )
        assert instance.engine_type == 'split_pipeline'

    def test_invalid_engine_type_pdfminer(self):
        with pytest.raises(ValidationError):
            EngineInstance(
                engine_type='pdfminer',
                name='pdfminer',
                config={},
            )

    def test_invalid_engine_type_unknown(self):
        with pytest.raises(ValidationError):
            EngineInstance(
                engine_type='unknown',
                name='Unknown',
                config={},
            )

    def test_commercial_api_with_invalid_provider(self):
        with pytest.raises(ValidationError):
            EngineInstance(
                engine_type='commercial_api',
                name='Bad Provider',
                config={
                    'provider': 'invalid_provider',
                    'api_key': 'key',
                },
            )

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            EngineInstance(
                engine_type='vllm',
                name='',
                config={'host': 'localhost', 'port': 8000},
            )

    def test_name_too_long_rejected(self):
        with pytest.raises(ValidationError):
            EngineInstance(
                engine_type='vllm',
                name='x' * 101,
                config={'host': 'localhost', 'port': 8000},
            )

    def test_vllm_config_with_defaults(self):
        instance = EngineInstance(
            engine_type='vllm',
            name='Default vLLM',
            config={},
        )
        assert instance.config == {}

    def test_commercial_api_with_custom_prompt(self):
        instance = EngineInstance(
            engine_type='commercial_api',
            name='Gemini Custom',
            config={
                'provider': 'gemini',
                'api_key': 'test-key',
                'model': 'gemini-3-flash-preview',
                'prompt': 'Extract all text from this image.',
            },
        )
        assert instance.config['prompt'] == 'Extract all text from this image.'

    def test_commercial_api_without_prompt_is_valid(self):
        instance = EngineInstance(
            engine_type='commercial_api',
            name='No Prompt Gemini',
            config={
                'provider': 'gemini',
                'api_key': 'test-key',
                'model': 'gemini-3-flash-preview',
            },
        )
        assert instance.engine_type == 'commercial_api'

    def test_commercial_api_requires_provider_field(self):
        with pytest.raises(ValidationError):
            EngineInstance(
                engine_type='commercial_api',
                name='Missing provider',
                config={'api_key': 'key'},
            )


class TestEngineInstanceCreate:
    def test_auto_generate_id(self):
        create = EngineInstanceCreate(
            engine_type='vllm',
            name='My vLLM Server',
            config={'host': 'localhost', 'port': 8000},
        )
        assert create.engine_id is None

    def test_custom_id(self):
        create = EngineInstanceCreate(
            engine_id='my-vllm',
            engine_type='vllm',
            name='My vLLM Server',
            config={'host': 'localhost', 'port': 8000},
        )
        assert create.engine_id == 'my-vllm'

    def test_invalid_custom_id_uppercase(self):
        with pytest.raises(ValidationError):
            EngineInstanceCreate(
                engine_id='MyVLLM',
                engine_type='vllm',
                name='My vLLM',
                config={'host': 'localhost'},
            )

    def test_invalid_custom_id_starts_with_hyphen(self):
        with pytest.raises(ValidationError):
            EngineInstanceCreate(
                engine_id='-my-vllm',
                engine_type='vllm',
                name='My vLLM',
                config={'host': 'localhost'},
            )


class TestEngineInstanceUpdate:
    def test_partial_update_name_only(self):
        update = EngineInstanceUpdate(name='New Name')
        assert update.name == 'New Name'
        assert update.config is None

    def test_partial_update_config_only(self):
        update = EngineInstanceUpdate(config={'host': 'new-host', 'port': 9000})
        assert update.name is None
        assert update.config == {'host': 'new-host', 'port': 9000}

    def test_full_update(self):
        update = EngineInstanceUpdate(
            name='Updated',
            config={'host': 'new-host'},
        )
        assert update.name == 'Updated'
        assert update.config is not None


class TestOcrConfigResponse:
    def test_empty_config(self):
        response = OcrConfigResponse()
        assert response.default_engine_id is None
        assert response.engines == {}

    def test_with_engines(self):
        response = OcrConfigResponse(
            default_engine_id='gemini-flash',
            engines={
                'gemini-flash': EngineInstance(
                    engine_type='commercial_api',
                    name='Gemini Flash',
                    config={
                        'provider': 'gemini',
                        'api_key': 'key',
                        'model': 'gemini-3-flash-preview',
                    },
                ),
            },
        )
        assert response.default_engine_id == 'gemini-flash'
        assert 'gemini-flash' in response.engines
