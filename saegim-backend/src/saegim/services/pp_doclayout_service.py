"""PP-DocLayoutV3 document layout detection service.

Uses PaddlePaddle's PP-DocLayoutV3 object detection model to detect layout
regions (bounding boxes + categories) from page images.  The model outputs
pixel-coordinate bounding boxes and 25 element categories.

Model: PaddlePaddle/PP-DocLayoutV3_safetensors (HuggingFace transformers).
"""

import importlib
import logging
from pathlib import Path
from typing import Any

from PIL import Image

from saegim.services.layout_types import LayoutRegion

logger = logging.getLogger(__name__)

# Mapping from PP-DocLayoutV3 labels to OmniDocBench category types.
# Labels sourced from config.json id2label (25 classes).
_LABEL_TO_CATEGORY: dict[str, str] = {
    'doc_title': 'title',
    'paragraph_title': 'title',
    'figure_title': 'title',
    'text': 'text_block',
    'content': 'text_block',
    'abstract': 'text_block',
    'aside_text': 'text_block',
    'table': 'table',
    'image': 'figure',
    'chart': 'figure',
    'formula': 'equation',
    'formula_number': 'equation',
    'header': 'header',
    'footer': 'footer',
    'footnote': 'footnote',
    'vision_footnote': 'footnote',
    'number': 'page_number',
    'reference': 'reference',
    'reference_content': 'reference',
    'algorithm': 'code',
}

_DEFAULT_MODEL = 'PaddlePaddle/PP-DocLayoutV3_safetensors'
_DEFAULT_THRESHOLD = 0.3


def parse_detections_to_regions(
    detections: list[dict[str, Any]],
) -> list[LayoutRegion]:
    """Convert raw detection dicts to LayoutRegion instances.

    Args:
        detections: List of dicts with 'label', 'score', 'box' keys.
            Each 'box' is ``[x1, y1, x2, y2]`` in pixel coordinates.

    Returns:
        List of LayoutRegion instances.
    """
    regions: list[LayoutRegion] = []
    for det in detections:
        label = det['label']
        category = _LABEL_TO_CATEGORY.get(label, 'unknown')
        box = det['box']
        regions.append(
            LayoutRegion(
                bbox=(float(box[0]), float(box[1]), float(box[2]), float(box[3])),
                category=category,
                score=float(det['score']),
            )
        )
    return regions


class PPDocLayoutV3Detector:
    """PP-DocLayoutV3 based document layout detector.

    Uses PaddlePaddle's PP-DocLayoutV3 object detection model for detecting
    text blocks, tables, figures, equations, and other document layout elements.
    Implements the LayoutDetector protocol.
    """

    def __init__(
        self,
        model_name: str = _DEFAULT_MODEL,
        *,
        threshold: float = _DEFAULT_THRESHOLD,
    ) -> None:
        """Initialize PPDocLayoutV3Detector with the specified model.

        Args:
            model_name: HuggingFace model identifier.
            threshold: Detection confidence threshold (0-1).
        """
        self.model_name = model_name
        self._threshold = threshold
        self._processor: Any = None
        self._model: Any = None
        self._device: str = 'cpu'

    def detect_layout(self, image_path: Path) -> list[LayoutRegion]:
        """Detect layout regions from a page image.

        Args:
            image_path: Path to the page image file.

        Returns:
            List of detected LayoutRegion instances.
        """
        self._ensure_model_loaded()
        detections = self._run_inference(image_path)
        return parse_detections_to_regions(detections)

    def test_connection(self) -> tuple[bool, str]:
        """Test that torch and transformers are available.

        Returns:
            Tuple of (success, message).
        """
        try:
            torch = importlib.import_module('torch')
            importlib.import_module('transformers')
        except (ImportError, ModuleNotFoundError):
            return (False, 'torch and transformers are required for PPDocLayoutV3Detector')

        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        return (True, f'PPDocLayoutV3Detector available (device: {device})')

    def _ensure_model_loaded(self) -> None:
        """Lazy-load the model and processor on first use.

        Raises:
            RuntimeError: If model loading fails.
        """
        if self._model is not None:
            return

        try:
            import torch
            from transformers import AutoImageProcessor, AutoModelForObjectDetection

            self._device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(
                'Loading PPDocLayoutV3 model %s on %s (CUDA available: %s)',
                self.model_name,
                self._device,
                torch.cuda.is_available(),
            )

            self._processor = AutoImageProcessor.from_pretrained(
                self.model_name,
                trust_remote_code=True,
            )
            self._model = AutoModelForObjectDetection.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16 if self._device == 'cuda' else torch.float32,
                trust_remote_code=True,
            ).to(self._device)

            logger.info('PPDocLayoutV3 model loaded successfully on %s', self._device)
        except ImportError as exc:
            msg = 'torch and transformers are required for PPDocLayoutV3Detector'
            raise ImportError(msg) from exc
        except Exception as exc:
            logger.exception('Failed to load PPDocLayoutV3 model %s', self.model_name)
            msg = f'Failed to load model {self.model_name}: {exc}'
            raise RuntimeError(msg) from exc

    def _run_inference(self, image_path: Path) -> list[dict[str, Any]]:
        """Run model inference on an image.

        Args:
            image_path: Path to the page image file.

        Returns:
            List of detection dicts with 'label', 'score', 'box' keys.
        """
        import torch

        image = Image.open(image_path)
        inputs = self._processor(images=image, return_tensors='pt').to(self._device)

        with torch.no_grad():
            outputs = self._model(**inputs)

        target_sizes = torch.tensor([image.size[::-1]], device=self._device)
        results = self._processor.post_process_object_detection(
            outputs,
            threshold=self._threshold,
            target_sizes=target_sizes,
        )[0]

        detections: list[dict[str, Any]] = []
        for score, label_id, box in zip(
            results['scores'],
            results['labels'],
            results['boxes'],
            strict=True,
        ):
            label = self._model.config.id2label[label_id.item()]
            detections.append(
                {
                    'label': label,
                    'score': score.item(),
                    'box': box.tolist(),
                }
            )

        return detections
