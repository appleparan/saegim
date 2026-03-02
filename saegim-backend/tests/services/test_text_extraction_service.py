"""Tests for text extraction service."""

import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from saegim.services.text_extraction_service import (
    NoTextProviderError,
    TextExtractionError,
    build_text_provider,
    crop_region,
    extract_text_from_region,
    poly_to_bbox,
    resolve_text_provider,
)


def _make_test_image(width: int = 800, height: int = 1200):
    """Create a simple test image."""
    return Image.new('RGB', (width, height), color='white')


def _make_test_image_path(tmp_path, width: int = 800, height: int = 1200):
    """Create a test image file and return its path."""
    img = _make_test_image(width, height)
    path = tmp_path / 'test_page.png'
    img.save(path, format='PNG')
    img.close()
    return path


class TestPolyToBbox:
    def test_basic_rectangle(self):
        poly = [10.0, 20.0, 100.0, 20.0, 100.0, 60.0, 10.0, 60.0]
        assert poly_to_bbox(poly) == (10.0, 20.0, 100.0, 60.0)

    def test_handles_non_axis_aligned(self):
        poly = [50.0, 10.0, 100.0, 50.0, 50.0, 100.0, 0.0, 50.0]
        x1, y1, x2, y2 = poly_to_bbox(poly)
        assert x1 == 0.0
        assert y1 == 10.0
        assert x2 == 100.0
        assert y2 == 100.0


class TestCropRegion:
    def test_basic_crop(self):
        img = _make_test_image(100, 100)
        result = crop_region(img, (10.0, 20.0, 50.0, 60.0))
        cropped = Image.open(io.BytesIO(result))
        assert cropped.size == (40, 40)
        img.close()
        cropped.close()

    def test_clamped_to_bounds(self):
        img = _make_test_image(100, 100)
        result = crop_region(img, (-10.0, -5.0, 200.0, 150.0))
        cropped = Image.open(io.BytesIO(result))
        assert cropped.size == (100, 100)
        img.close()
        cropped.close()

    def test_zero_area_raises_error(self):
        img = _make_test_image(100, 100)
        with pytest.raises(TextExtractionError, match='zero area'):
            crop_region(img, (50.0, 50.0, 50.0, 50.0))
        img.close()

    def test_returns_png_bytes(self):
        img = _make_test_image(100, 100)
        result = crop_region(img, (0.0, 0.0, 50.0, 50.0))
        # PNG magic bytes
        assert result[:4] == b'\x89PNG'
        img.close()


class TestBuildTextProvider:
    def test_split_pipeline_gemini(self):
        config = {
            'engine_type': 'split_pipeline',
            'split_pipeline': {
                'ocr_provider': 'gemini',
                'ocr_api_key': 'test-key',
                'ocr_model': 'gemini-3-flash-preview',
            },
        }
        provider = build_text_provider(config)
        assert provider is not None
        assert hasattr(provider, 'extract_text')

    def test_split_pipeline_vllm(self):
        config = {
            'engine_type': 'split_pipeline',
            'split_pipeline': {
                'ocr_provider': 'vllm',
                'ocr_host': 'localhost',
                'ocr_port': 8000,
            },
        }
        provider = build_text_provider(config)
        assert provider is not None

    def test_commercial_api_gemini(self):
        config = {
            'engine_type': 'commercial_api',
            'commercial_api': {
                'provider': 'gemini',
                'api_key': 'test-key',
            },
        }
        provider = build_text_provider(config)
        assert provider is not None

    def test_vllm(self):
        config = {
            'engine_type': 'vllm',
            'vllm': {
                'host': 'localhost',
                'port': 8000,
                'model': 'datalab-to/chandra',
            },
        }
        provider = build_text_provider(config)
        assert provider is not None

    def test_pdfminer_returns_none(self):
        config = {'engine_type': 'pdfminer'}
        assert build_text_provider(config) is None

    def test_unknown_engine_returns_none(self):
        config = {'engine_type': 'unknown'}
        assert build_text_provider(config) is None

    def test_empty_config_returns_none(self):
        assert build_text_provider({}) is None

    def test_gemini_without_api_key_returns_none(self):
        config = {
            'engine_type': 'commercial_api',
            'commercial_api': {
                'provider': 'gemini',
            },
        }
        assert build_text_provider(config) is None

    def test_engine_id_uses_override(self):
        config = {
            'engine_type': 'pdfminer',
            'vllm': {
                'host': 'localhost',
                'port': 8000,
                'model': 'datalab-to/chandra',
            },
        }
        # Default engine is pdfminer (returns None), but override to vllm
        provider = build_text_provider(config, engine_id='vllm')
        assert provider is not None

    def test_engine_id_none_uses_default(self):
        config = {'engine_type': 'pdfminer'}
        provider = build_text_provider(config, engine_id=None)
        assert provider is None

    def test_engine_id_commercial_api(self):
        config = {
            'engine_type': 'vllm',
            'vllm': {'host': 'localhost', 'port': 8000},
            'commercial_api': {
                'provider': 'gemini',
                'api_key': 'test-key',
                'model': 'gemini-3-flash-preview',
            },
        }
        # Override to commercial_api even though default is vllm
        provider = build_text_provider(config, engine_id='commercial_api')
        assert provider is not None
        assert hasattr(provider, 'extract_text')

    def test_engine_id_to_pdfminer_returns_none(self):
        config = {
            'engine_type': 'commercial_api',
            'commercial_api': {
                'provider': 'gemini',
                'api_key': 'test-key',
            },
        }
        # Override to pdfminer (no region-level extraction)
        provider = build_text_provider(config, engine_id='pdfminer')
        assert provider is None

    def test_engine_id_missing_sub_config(self):
        config = {
            'engine_type': 'pdfminer',
            # No commercial_api sub-config present
        }
        # Override to commercial_api, but no sub-config → gemini with no key → None
        provider = build_text_provider(config, engine_id='commercial_api')
        assert provider is None


class TestBuildTextProviderMultiInstance:
    """Tests for build_text_provider with new multi-instance format."""

    def test_uses_default_engine(self):
        config = {
            'default_engine_id': 'my-vllm',
            'engines': {
                'my-vllm': {
                    'engine_type': 'vllm',
                    'name': 'My vLLM',
                    'config': {'host': 'localhost', 'port': 8000, 'model': 'test'},
                },
            },
        }
        provider = build_text_provider(config)
        assert provider is not None

    def test_engine_id_overrides_default(self):
        config = {
            'default_engine_id': 'my-vllm',
            'engines': {
                'my-vllm': {
                    'engine_type': 'vllm',
                    'name': 'My vLLM',
                    'config': {'host': 'localhost', 'port': 8000},
                },
                'gemini-flash': {
                    'engine_type': 'commercial_api',
                    'name': 'Gemini Flash',
                    'config': {'provider': 'gemini', 'api_key': 'k', 'model': 'm'},
                },
            },
        }
        provider = build_text_provider(config, engine_id='gemini-flash')
        assert provider is not None

    def test_no_default_no_override_returns_none(self):
        config = {
            'default_engine_id': None,
            'engines': {
                'my-vllm': {
                    'engine_type': 'vllm',
                    'name': 'My vLLM',
                    'config': {'host': 'localhost', 'port': 8000},
                },
            },
        }
        provider = build_text_provider(config)
        assert provider is None

    def test_pdfminer_default_returns_none(self):
        config = {
            'default_engine_id': 'pdfminer',
            'engines': {},
        }
        provider = build_text_provider(config)
        assert provider is None

    def test_unknown_engine_id_returns_none(self):
        config = {
            'default_engine_id': 'nonexistent',
            'engines': {},
        }
        provider = build_text_provider(config)
        assert provider is None

    def test_commercial_api_gemini(self):
        config = {
            'default_engine_id': 'gemini-pro',
            'engines': {
                'gemini-pro': {
                    'engine_type': 'commercial_api',
                    'name': 'Gemini Pro',
                    'config': {'provider': 'gemini', 'api_key': 'test-key', 'model': 'pro'},
                },
            },
        }
        provider = build_text_provider(config)
        assert provider is not None

    def test_split_pipeline(self):
        config = {
            'default_engine_id': 'docling-ocr',
            'engines': {
                'docling-ocr': {
                    'engine_type': 'split_pipeline',
                    'name': 'Docling OCR',
                    'config': {
                        'ocr_provider': 'vllm',
                        'ocr_host': 'localhost',
                        'ocr_port': 8000,
                    },
                },
            },
        }
        provider = build_text_provider(config)
        assert provider is not None


class TestExtractTextFromRegion:
    def test_success(self, tmp_path):
        image_path = _make_test_image_path(tmp_path)
        poly = [10.0, 20.0, 100.0, 20.0, 100.0, 60.0, 10.0, 60.0]
        mock_provider = MagicMock()
        mock_provider.extract_text.return_value = 'Hello world'

        result = extract_text_from_region(image_path, poly, 'text_block', mock_provider)

        assert result == 'Hello world'
        mock_provider.extract_text.assert_called_once()
        call_args = mock_provider.extract_text.call_args
        assert call_args[0][1] == 'text_block'
        # First arg should be PNG bytes
        assert call_args[0][0][:4] == b'\x89PNG'

    def test_image_not_found_raises_error(self, tmp_path):
        poly = [10.0, 20.0, 100.0, 20.0, 100.0, 60.0, 10.0, 60.0]
        mock_provider = MagicMock()
        with pytest.raises(TextExtractionError, match='Failed to open image'):
            extract_text_from_region(
                tmp_path / 'nonexistent.png', poly, 'text_block', mock_provider
            )

    def test_ocr_provider_failure_raises_error(self, tmp_path):
        image_path = _make_test_image_path(tmp_path)
        poly = [10.0, 20.0, 100.0, 20.0, 100.0, 60.0, 10.0, 60.0]
        mock_provider = MagicMock()
        mock_provider.extract_text.side_effect = RuntimeError('API timeout')

        with pytest.raises(TextExtractionError, match='OCR provider failed'):
            extract_text_from_region(image_path, poly, 'text_block', mock_provider)

    def test_zero_area_region_raises_error(self, tmp_path):
        image_path = _make_test_image_path(tmp_path)
        # Degenerate polygon (all same point)
        poly = [50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0]
        mock_provider = MagicMock()

        with pytest.raises(TextExtractionError, match='zero area'):
            extract_text_from_region(image_path, poly, 'text_block', mock_provider)

    def test_table_category_passes_hint(self, tmp_path):
        image_path = _make_test_image_path(tmp_path)
        poly = [0.0, 0.0, 100.0, 0.0, 100.0, 100.0, 0.0, 100.0]
        mock_provider = MagicMock()
        mock_provider.extract_text.return_value = '| A | B |'

        extract_text_from_region(image_path, poly, 'table', mock_provider)
        assert mock_provider.extract_text.call_args[0][1] == 'table'


class TestResolveTextProvider:
    @pytest.fixture
    def mock_pool(self):
        pool = MagicMock()
        pool.fetchrow = AsyncMock()
        pool.fetch = AsyncMock()
        return pool

    @pytest.fixture
    def page_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def project_id(self):
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_override_uses_different_engine(self, mock_pool, page_id, project_id):
        page_record = {
            'image_path': '/storage/images/test.png',
            'project_id': project_id,
        }
        ocr_config = {
            'engine_type': 'pdfminer',
            'vllm': {'host': 'localhost', 'port': 8000, 'model': 'test-model'},
        }
        with (
            patch(
                'saegim.repositories.page_repo.get_by_id_with_context',
                new_callable=AsyncMock,
                return_value=page_record,
            ),
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=ocr_config,
            ),
        ):
            _, provider = await resolve_text_provider(mock_pool, page_id, engine_id='vllm')
        assert provider is not None

    @pytest.mark.asyncio
    async def test_override_none_uses_project_default(self, mock_pool, page_id, project_id):
        page_record = {
            'image_path': '/storage/images/test.png',
            'project_id': project_id,
        }
        ocr_config = {'engine_type': 'pdfminer'}
        with (
            patch(
                'saegim.repositories.page_repo.get_by_id_with_context',
                new_callable=AsyncMock,
                return_value=page_record,
            ),
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=ocr_config,
            ),
            pytest.raises(NoTextProviderError, match='pdfminer'),
        ):
            await resolve_text_provider(mock_pool, page_id, engine_id=None)

    @pytest.mark.asyncio
    async def test_page_not_found_raises_lookup_error(self, mock_pool, page_id):
        with (
            patch(
                'saegim.repositories.page_repo.get_by_id_with_context',
                new_callable=AsyncMock,
                return_value=None,
            ),
            pytest.raises(LookupError, match='Page not found'),
        ):
            await resolve_text_provider(mock_pool, page_id)

    @pytest.mark.asyncio
    async def test_override_to_unsupported_engine_raises_error(
        self, mock_pool, page_id, project_id
    ):
        page_record = {
            'image_path': '/storage/images/test.png',
            'project_id': project_id,
        }
        ocr_config = {
            'engine_type': 'commercial_api',
            'commercial_api': {
                'provider': 'gemini',
                'api_key': 'test-key',
            },
        }
        with (
            patch(
                'saegim.repositories.page_repo.get_by_id_with_context',
                new_callable=AsyncMock,
                return_value=page_record,
            ),
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=ocr_config,
            ),
            pytest.raises(NoTextProviderError, match='pdfminer'),
        ):
            await resolve_text_provider(mock_pool, page_id, engine_id='pdfminer')

    @pytest.mark.asyncio
    async def test_multi_instance_default_engine(self, mock_pool, page_id, project_id):
        page_record = {
            'image_path': '/storage/images/test.png',
            'project_id': project_id,
        }
        ocr_config = {
            'default_engine_id': 'my-vllm',
            'engines': {
                'my-vllm': {
                    'engine_type': 'vllm',
                    'name': 'My vLLM',
                    'config': {'host': 'localhost', 'port': 8000, 'model': 'test'},
                },
            },
        }
        with (
            patch(
                'saegim.repositories.page_repo.get_by_id_with_context',
                new_callable=AsyncMock,
                return_value=page_record,
            ),
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=ocr_config,
            ),
        ):
            _, provider = await resolve_text_provider(mock_pool, page_id)
        assert provider is not None

    @pytest.mark.asyncio
    async def test_multi_instance_engine_id_override(self, mock_pool, page_id, project_id):
        page_record = {
            'image_path': '/storage/images/test.png',
            'project_id': project_id,
        }
        ocr_config = {
            'default_engine_id': 'my-vllm',
            'engines': {
                'my-vllm': {
                    'engine_type': 'vllm',
                    'name': 'My vLLM',
                    'config': {'host': 'localhost', 'port': 8000},
                },
                'gemini-flash': {
                    'engine_type': 'commercial_api',
                    'name': 'Gemini Flash',
                    'config': {'provider': 'gemini', 'api_key': 'k', 'model': 'm'},
                },
            },
        }
        with (
            patch(
                'saegim.repositories.page_repo.get_by_id_with_context',
                new_callable=AsyncMock,
                return_value=page_record,
            ),
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=ocr_config,
            ),
        ):
            _, provider = await resolve_text_provider(mock_pool, page_id, engine_id='gemini-flash')
        assert provider is not None

    @pytest.mark.asyncio
    async def test_multi_instance_no_config_raises(self, mock_pool, page_id, project_id):
        page_record = {
            'image_path': '/storage/images/test.png',
            'project_id': project_id,
        }
        with (
            patch(
                'saegim.repositories.page_repo.get_by_id_with_context',
                new_callable=AsyncMock,
                return_value=page_record,
            ),
            patch(
                'saegim.repositories.project_repo.get_ocr_config',
                new_callable=AsyncMock,
                return_value=None,
            ),
            pytest.raises(NoTextProviderError),
        ):
            await resolve_text_provider(mock_pool, page_id)
