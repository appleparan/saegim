"""Tests for PPDocLayoutV3Detector."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from saegim.services.layout_types import LayoutRegion
from saegim.services.pp_doclayout_service import (
    _LABEL_TO_CATEGORY,
    PPDocLayoutV3Detector,
    parse_detections_to_regions,
)

_MODULE = 'saegim.services.pp_doclayout_service'


class TestLabelMapping:
    def test_doc_title_maps_to_title(self):
        assert _LABEL_TO_CATEGORY['doc_title'] == 'title'

    def test_paragraph_title_maps_to_title(self):
        assert _LABEL_TO_CATEGORY['paragraph_title'] == 'title'

    def test_text_maps_to_text_block(self):
        assert _LABEL_TO_CATEGORY['text'] == 'text_block'

    def test_table_maps_to_table(self):
        assert _LABEL_TO_CATEGORY['table'] == 'table'

    def test_image_maps_to_figure(self):
        assert _LABEL_TO_CATEGORY['image'] == 'figure'

    def test_formula_maps_to_equation(self):
        assert _LABEL_TO_CATEGORY['formula'] == 'equation'

    def test_header_maps_to_header(self):
        assert _LABEL_TO_CATEGORY['header'] == 'header'

    def test_footer_maps_to_footer(self):
        assert _LABEL_TO_CATEGORY['footer'] == 'footer'

    def test_footnote_maps_to_footnote(self):
        assert _LABEL_TO_CATEGORY['footnote'] == 'footnote'

    def test_chart_maps_to_figure(self):
        assert _LABEL_TO_CATEGORY['chart'] == 'figure'


class TestParseDetectionsToRegions:
    def test_basic_detections(self):
        detections = [
            {'label': 'text', 'score': 0.9, 'box': [10.0, 20.0, 300.0, 100.0]},
            {'label': 'table', 'score': 0.85, 'box': [10.0, 120.0, 300.0, 400.0]},
        ]
        regions = parse_detections_to_regions(detections)

        assert len(regions) == 2
        assert regions[0].category == 'text_block'
        assert regions[0].bbox == (10.0, 20.0, 300.0, 100.0)
        assert regions[0].score == 0.9
        assert regions[0].text is None
        assert regions[1].category == 'table'

    def test_empty_detections(self):
        assert parse_detections_to_regions([]) == []

    def test_unknown_label_maps_to_unknown(self):
        detections = [
            {'label': 'seal', 'score': 0.7, 'box': [0.0, 0.0, 50.0, 50.0]},
        ]
        regions = parse_detections_to_regions(detections)
        assert regions[0].category == 'unknown'

    def test_all_regions_have_no_text(self):
        detections = [
            {'label': 'text', 'score': 0.9, 'box': [0.0, 0.0, 100.0, 50.0]},
            {'label': 'image', 'score': 0.8, 'box': [0.0, 60.0, 100.0, 200.0]},
        ]
        regions = parse_detections_to_regions(detections)
        for region in regions:
            assert region.text is None

    def test_returns_layout_region_instances(self):
        detections = [
            {'label': 'text', 'score': 0.9, 'box': [10.0, 20.0, 300.0, 100.0]},
        ]
        regions = parse_detections_to_regions(detections)
        assert isinstance(regions[0], LayoutRegion)

    def test_score_preserved(self):
        detections = [
            {'label': 'formula', 'score': 0.42, 'box': [0.0, 0.0, 50.0, 30.0]},
        ]
        regions = parse_detections_to_regions(detections)
        assert regions[0].score == pytest.approx(0.42)

    def test_multiple_title_types(self):
        detections = [
            {'label': 'doc_title', 'score': 0.95, 'box': [10.0, 10.0, 500.0, 60.0]},
            {'label': 'paragraph_title', 'score': 0.88, 'box': [10.0, 80.0, 400.0, 110.0]},
        ]
        regions = parse_detections_to_regions(detections)
        assert regions[0].category == 'title'
        assert regions[1].category == 'title'


class TestPPDocLayoutV3DetectorInit:
    def test_default_model_name(self):
        detector = PPDocLayoutV3Detector()
        assert detector.model_name == 'PaddlePaddle/PP-DocLayoutV3_safetensors'

    def test_custom_model_name(self):
        detector = PPDocLayoutV3Detector(model_name='custom/model')
        assert detector.model_name == 'custom/model'

    def test_lazy_loading(self):
        detector = PPDocLayoutV3Detector()
        assert detector._model is None
        assert detector._processor is None


class TestPPDocLayoutV3DetectorDetectLayout:
    @patch(f'{_MODULE}.PPDocLayoutV3Detector._ensure_model_loaded')
    @patch(f'{_MODULE}.PPDocLayoutV3Detector._run_inference')
    def test_returns_layout_regions(self, mock_inference, mock_load):
        mock_inference.return_value = [
            {'label': 'text', 'score': 0.9, 'box': [10.0, 20.0, 300.0, 100.0]},
            {'label': 'image', 'score': 0.85, 'box': [10.0, 120.0, 300.0, 400.0]},
        ]

        detector = PPDocLayoutV3Detector()
        regions = detector.detect_layout(Path('/fake/image.png'))

        mock_load.assert_called_once()
        assert len(regions) == 2
        assert regions[0].category == 'text_block'
        assert regions[1].category == 'figure'

    @patch(f'{_MODULE}.PPDocLayoutV3Detector._ensure_model_loaded')
    @patch(f'{_MODULE}.PPDocLayoutV3Detector._run_inference')
    def test_empty_detections(self, mock_inference, mock_load):
        mock_inference.return_value = []

        detector = PPDocLayoutV3Detector()
        regions = detector.detect_layout(Path('/fake/image.png'))

        assert regions == []


class TestPPDocLayoutV3DetectorTestConnection:
    @patch(f'{_MODULE}.importlib')
    def test_success_with_cuda(self, mock_importlib):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_importlib.import_module.side_effect = lambda _name: mock_torch

        detector = PPDocLayoutV3Detector()
        success, message = detector.test_connection()

        assert success is True
        assert 'cuda' in message

    @patch(f'{_MODULE}.importlib')
    def test_success_without_cuda(self, mock_importlib):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_importlib.import_module.side_effect = lambda _name: mock_torch

        detector = PPDocLayoutV3Detector()
        success, message = detector.test_connection()

        assert success is True
        assert 'cpu' in message

    @patch(f'{_MODULE}.importlib')
    def test_missing_dependencies(self, mock_importlib):
        mock_importlib.import_module.side_effect = ImportError('No module')

        detector = PPDocLayoutV3Detector()
        success, message = detector.test_connection()

        assert success is False
        assert 'torch' in message or 'transformers' in message
