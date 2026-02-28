"""Auto attribute classifier for OCR extraction results.

Classifies page-level and element-level attributes from text content
and coordinate data. Runs as a post-processing step after OCR extraction.

Classification strategies:
- Language: Unicode character range analysis
- Layout: X-coordinate clustering of text blocks
- Data source: Keyword heuristics
- Table structure: HTML parsing for spans, aspect ratio analysis
- Math detection: LaTeX pattern matching
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# --- Unicode range constants ---

_HANGUL_RANGES = (
    (0xAC00, 0xD7AF),  # Hangul Syllables
    (0x1100, 0x11FF),  # Hangul Jamo
    (0x3130, 0x318F),  # Hangul Compatibility Jamo
)

_CJK_RANGE = (0x4E00, 0x9FFF)

_LATIN_RANGES = (
    (0x0041, 0x005A),  # Basic Latin uppercase
    (0x0061, 0x007A),  # Basic Latin lowercase
    (0x00C0, 0x024F),  # Latin Extended
)

# --- Data source keyword rules (priority order) ---

_DATA_SOURCE_RULES: list[tuple[str, list[str]]] = [
    (
        'academic_literature',
        [
            r'\bAbstract\b',
            r'\bReferences?\b',
            r'\bIntroduction\b',
            r'\b초록\b',
            r'\b참고문헌\b',
            r'\b서론\b',
            r'\barXiv\b',
            r'\bDOI\b',
            r'\bISSN\b',
        ],
    ),
    (
        'exam_paper',
        [
            r'시험',
            r'수능',
            r'모의고사',
            r'\bExam\b',
        ],
    ),
    (
        'government_doc',
        [
            r'공문',
            r'시행일',
            r'관보',
            r'고시',
        ],
    ),
    (
        'financial_report_kr',
        [
            r'재무제표',
            r'감사보고서',
            r'사업보고서',
            r'손익계산서',
            r'대차대조표',
        ],
    ),
    (
        'research_report',
        [
            r'연구보고서',
            r'\bResearch\s+Report\b',
            r'정책\s*보고서',
        ],
    ),
    (
        'newspaper',
        [
            r'기자',
            r'특파원',
            r'사설',
        ],
    ),
    (
        'book',
        [
            r'\bChapter\s+\d+\b',
            r'제\s*\d+\s*장',
            r'\bISBN\b',
        ],
    ),
    (
        'PPT2PDF',
        [
            r'\bSlide\s+\d+\b',
            r'슬라이드',
        ],
    ),
]

# --- LaTeX / math patterns ---

_MATH_PATTERNS = [
    r'\\frac\{',
    r'\\sum',
    r'\\int',
    r'\\alpha',
    r'\\beta',
    r'\\sqrt',
    r'\\mathbb',
    r'\\mathcal',
    r'\\left',
    r'\\right',
    r'\\times',
    r'\\cdot',
    r'\\pm',
    r'\\leq',
    r'\\geq',
    r'\$[^$]+\$',
]

_MATH_RE = re.compile('|'.join(_MATH_PATTERNS))

# Minimum character count to attempt language classification
_MIN_CHARS_FOR_LANG = 5

# Threshold for single-language dominance
_DOMINANT_RATIO = 0.7

# Mixed language minimum ratio
_MIXED_MIN_RATIO = 0.1

# Page layout constants
_TEXT_CATEGORIES = frozenset({'text_block', 'title'})
_FULL_WIDTH_RATIO = 0.6
_COLUMN_GAP_RATIO = 0.15


# ============================================================
# Public API
# ============================================================


def classify_attributes(extracted: dict[str, Any]) -> dict[str, Any]:
    """Classify page-level and element-level attributes for extracted data.

    Takes an OmniDocBench-compatible extraction result and populates:
    - page_attribute: language, layout, data_source
    - Each element's attribute dict based on category_type

    Uses a fill-missing strategy: existing non-empty attribute values
    are preserved; only missing or empty fields are auto-classified.

    Args:
        extracted: OmniDocBench dict with layout_dets, page_attribute, extra.

    Returns:
        The same dict with page_attribute and element attributes populated.
    """
    layout_dets = extracted.get('layout_dets', [])

    # Page-level: fill missing fields only
    existing_page_attr = extracted.get('page_attribute') or {}
    auto_page_attr = _classify_page_attributes(layout_dets)
    for key, value in auto_page_attr.items():
        if not existing_page_attr.get(key):
            existing_page_attr[key] = value
    extracted['page_attribute'] = existing_page_attr

    # Element-level: fill missing attribute keys
    for element in layout_dets:
        existing_attr = element.get('attribute') or {}
        auto_attr = _classify_element_attributes(element)
        for key, value in auto_attr.items():
            if key not in existing_attr or existing_attr[key] == '':
                existing_attr[key] = value
        element['attribute'] = existing_attr

    return extracted


# ============================================================
# Page-level classification
# ============================================================


def _classify_page_attributes(layout_dets: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify all page-level attributes from layout elements.

    Args:
        layout_dets: List of layout element dicts.

    Returns:
        PageAttribute-compatible dict.
    """
    return {
        'language': _classify_page_language(layout_dets),
        'layout': _classify_page_layout(layout_dets),
        'data_source': _classify_data_source(layout_dets),
        'watermark': False,  # TODO: requires image analysis
        'fuzzy_scan': False,  # TODO: requires image analysis
        'colorful_background': False,  # TODO: requires image analysis
    }


def _classify_page_language(layout_dets: list[dict[str, Any]]) -> str:
    """Classify page language from all extracted text.

    Args:
        layout_dets: List of layout element dicts.

    Returns:
        Language string: ko, en, ko_en_mixed, ko_ch_mixed, or empty.
    """
    text = _collect_all_text(layout_dets)
    counts = _count_unicode_ranges(text)

    total = counts['total_alpha']
    if total < _MIN_CHARS_FOR_LANG:
        return ''

    ko_ratio = counts['hangul'] / total
    en_ratio = counts['latin'] / total
    cjk_ratio = counts['cjk'] / total

    if ko_ratio >= _DOMINANT_RATIO:
        return 'ko'
    if en_ratio >= _DOMINANT_RATIO:
        return 'en'
    if ko_ratio >= _MIXED_MIN_RATIO and cjk_ratio >= _MIXED_MIN_RATIO:
        return 'ko_ch_mixed'
    if ko_ratio >= _MIXED_MIN_RATIO and en_ratio >= _MIXED_MIN_RATIO:
        return 'ko_en_mixed'

    # Fallback: most characters decide
    if ko_ratio >= en_ratio:
        return 'ko'
    return 'en'


def _classify_page_layout(layout_dets: list[dict[str, Any]]) -> str:
    """Classify page layout (column structure) from element positions.

    Uses x-coordinate gap analysis on text blocks to detect columns.

    Args:
        layout_dets: List of layout element dicts.

    Returns:
        Layout string: single_column, double_column, three_column,
        1andmore_column, or other_layout.
    """
    text_elements = [
        el
        for el in layout_dets
        if el.get('category_type') in _TEXT_CATEGORIES and len(el.get('poly', [])) >= 8
    ]

    if len(text_elements) < 2:
        return 'single_column'

    # Compute page width from all elements
    all_right_edges = []
    all_left_edges = []
    for el in layout_dets:
        poly = el.get('poly', [])
        if len(poly) >= 8:
            x_left = min(poly[0], poly[6])
            x_right = max(poly[2], poly[4])
            all_right_edges.append(x_right)
            all_left_edges.append(x_left)

    if not all_right_edges:
        return 'single_column'

    page_width = max(all_right_edges) - min(all_left_edges)
    if page_width <= 0:
        return 'single_column'

    page_left = min(all_left_edges)

    # Classify each text element as full-width or narrow
    full_width_count = 0
    narrow_x_centers: list[float] = []

    for el in text_elements:
        poly = el['poly']
        x_left = min(poly[0], poly[6])
        x_right = max(poly[2], poly[4])
        el_width = x_right - x_left

        if el_width >= page_width * _FULL_WIDTH_RATIO:
            full_width_count += 1
        else:
            x_center = (x_left + x_right) / 2.0
            narrow_x_centers.append(x_center)

    if not narrow_x_centers:
        return 'single_column'

    # Cluster narrow elements by x-center using gap-based approach
    num_columns = _count_column_clusters(narrow_x_centers, page_width, page_left)

    has_full_width = full_width_count > 0

    if num_columns <= 1 and not has_full_width:
        return 'single_column'
    if num_columns <= 1 and has_full_width:
        return 'single_column'
    if num_columns == 2 and has_full_width:
        return '1andmore_column'
    if num_columns == 2:
        return 'double_column'
    if num_columns == 3 and has_full_width:
        return '1andmore_column'
    if num_columns == 3:
        return 'three_column'
    return 'other_layout'


def _count_column_clusters(
    x_centers: list[float],
    page_width: float,
    _page_left: float,
) -> int:
    """Count the number of column clusters from x-center positions.

    Uses gap-based 1D clustering: sorts x-centers and splits at gaps
    larger than a threshold.

    Args:
        x_centers: List of x-center coordinates.
        page_width: Total page width.
        _page_left: Left edge of the page (unused, kept for interface).

    Returns:
        Number of detected column clusters.
    """
    if not x_centers:
        return 0

    sorted_centers = sorted(x_centers)
    gap_threshold = page_width * _COLUMN_GAP_RATIO

    clusters = 1
    for i in range(1, len(sorted_centers)):
        if sorted_centers[i] - sorted_centers[i - 1] > gap_threshold:
            clusters += 1

    return clusters


def _classify_data_source(layout_dets: list[dict[str, Any]]) -> str:
    """Classify document data source using keyword heuristics.

    Checks extracted text against priority-ordered keyword rules.
    Returns the first matching data source.

    Args:
        layout_dets: List of layout element dicts.

    Returns:
        Data source string or empty if no match.
    """
    text = _collect_all_text(layout_dets)
    if not text:
        return ''

    for data_source, patterns in _DATA_SOURCE_RULES:
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.debug('Data source matched: %s (pattern: %s)', data_source, pattern)
                return data_source

    return ''


# ============================================================
# Element-level classification
# ============================================================


def _classify_element_attributes(element: dict[str, Any]) -> dict[str, Any]:
    """Classify element-level attributes based on category type.

    Args:
        element: Layout element dict with category_type, text, html, etc.

    Returns:
        Attribute dict for the element's category. Empty dict for
        categories without defined attributes.
    """
    category = element.get('category_type', '')

    if category in ('text_block', 'title'):
        return _classify_text_attributes(element)
    if category == 'table':
        return _classify_table_attributes(element)
    if category == 'equation_isolated':
        return _classify_equation_attributes(element)

    return {}


def _classify_text_attributes(element: dict[str, Any]) -> dict[str, Any]:
    """Classify attributes for text_block or title elements.

    Args:
        element: Layout element dict.

    Returns:
        Attribute dict with text_language, text_background, text_rotate.
    """
    text = element.get('text', '')
    return {
        'text_language': _classify_text_language(text),
        'text_background': 'white',  # TODO: requires image analysis
        'text_rotate': 'normal',  # TODO: requires image analysis
    }


def _classify_text_language(text: str) -> str:
    """Classify language of a text block.

    Args:
        text: Text content.

    Returns:
        text_ko, text_en, text_ko_en_mixed, or empty string.
    """
    counts = _count_unicode_ranges(text)
    total = counts['total_alpha']

    if total < _MIN_CHARS_FOR_LANG:
        return ''

    ko_ratio = counts['hangul'] / total
    en_ratio = counts['latin'] / total

    if ko_ratio >= _DOMINANT_RATIO:
        return 'text_ko'
    if en_ratio >= _DOMINANT_RATIO:
        return 'text_en'
    if ko_ratio >= _MIXED_MIN_RATIO and en_ratio >= _MIXED_MIN_RATIO:
        return 'text_ko_en_mixed'

    if ko_ratio >= en_ratio:
        return 'text_ko'
    return 'text_en'


def _classify_table_attributes(element: dict[str, Any]) -> dict[str, Any]:
    """Classify attributes for table elements.

    Args:
        element: Layout element dict with html, text, poly fields.

    Returns:
        Attribute dict with table_layout, with_span, line, language, etc.
    """
    html = element.get('html', '')
    poly = element.get('poly', [])

    return {
        'table_layout': _classify_table_layout(poly),
        'with_span': _detect_table_span(html),
        'line': '',  # TODO: requires image analysis
        'language': _classify_table_language(element),
        'include_equation': _detect_equation_in_table(element),
        'include_background': False,  # TODO: requires image analysis
        'table_vertical': _detect_table_vertical(poly),
    }


def _classify_table_layout(poly: list[float]) -> str:
    """Classify table layout direction from bounding box aspect ratio.

    Args:
        poly: 8-float polygon [x1,y1, x2,y2, x3,y3, x4,y4].

    Returns:
        'vertical' or 'horizontal'.
    """
    if len(poly) < 8:
        return 'horizontal'

    width = max(poly[2], poly[4]) - min(poly[0], poly[6])
    height = max(poly[5], poly[7]) - min(poly[1], poly[3])

    if width > 0 and height > width * 1.5:
        return 'vertical'
    return 'horizontal'


def _detect_table_span(html: str) -> bool:
    """Detect merged cells (colspan/rowspan) in table HTML.

    Args:
        html: Table HTML string.

    Returns:
        True if colspan or rowspan attributes are found.
    """
    if not html:
        return False
    return bool(re.search(r'(?:colspan|rowspan)\s*=\s*["\']?\d+', html, re.IGNORECASE))


def _classify_table_language(element: dict[str, Any]) -> str:
    """Classify language of table content.

    Args:
        element: Table element dict.

    Returns:
        table_ko, table_en, table_ko_en_mixed, or empty string.
    """
    text = element.get('text', '')
    html = element.get('html', '')

    combined = text + ' ' + _strip_html_tags(html)
    counts = _count_unicode_ranges(combined)
    total = counts['total_alpha']

    if total < _MIN_CHARS_FOR_LANG:
        return ''

    ko_ratio = counts['hangul'] / total
    en_ratio = counts['latin'] / total

    if ko_ratio >= _DOMINANT_RATIO:
        return 'table_ko'
    if en_ratio >= _DOMINANT_RATIO:
        return 'table_en'
    if ko_ratio >= _MIXED_MIN_RATIO and en_ratio >= _MIXED_MIN_RATIO:
        return 'table_ko_en_mixed'

    if ko_ratio >= en_ratio:
        return 'table_ko'
    return 'table_en'


def _detect_equation_in_table(element: dict[str, Any]) -> bool:
    """Detect LaTeX or math patterns in table content.

    Args:
        element: Table element dict.

    Returns:
        True if math patterns are found.
    """
    text = element.get('text', '')
    html = element.get('html', '')
    latex = element.get('latex', '')

    combined = text + ' ' + html + ' ' + latex
    return bool(_MATH_RE.search(combined))


def _detect_table_vertical(poly: list[float]) -> bool:
    """Detect if a table is vertically rotated based on aspect ratio.

    A strongly vertical table (height > 2x width) suggests rotation.

    Args:
        poly: 8-float polygon.

    Returns:
        True if table appears vertically rotated.
    """
    if len(poly) < 8:
        return False

    width = max(poly[2], poly[4]) - min(poly[0], poly[6])
    height = max(poly[5], poly[7]) - min(poly[1], poly[3])

    return width > 0 and height > width * 2.0


def _classify_equation_attributes(element: dict[str, Any]) -> dict[str, Any]:
    """Classify attributes for equation_isolated elements.

    Args:
        element: Equation element dict with latex, text fields.

    Returns:
        Attribute dict with formula_type and equation_language.
    """
    return {
        'formula_type': 'print',  # TODO: handwriting detection requires image analysis
        'equation_language': _classify_equation_language(element),
    }


def _classify_equation_language(element: dict[str, Any]) -> str:
    """Classify equation language from latex/text content.

    Args:
        element: Equation element dict.

    Returns:
        equation_ko if Korean characters found, else equation_en.
    """
    latex = element.get('latex', '')
    text = element.get('text', '')
    combined = latex + ' ' + text

    for ch in combined:
        cp = ord(ch)
        if any(start <= cp <= end for start, end in _HANGUL_RANGES):
            return 'equation_ko'

    return 'equation_en'


# ============================================================
# Shared helpers
# ============================================================


def _count_unicode_ranges(text: str) -> dict[str, int]:
    """Count characters by Unicode range category.

    Args:
        text: Input text string.

    Returns:
        Dict with keys: hangul, cjk, latin, total_alpha.
    """
    hangul = 0
    cjk = 0
    latin = 0

    for ch in text:
        cp = ord(ch)
        if any(start <= cp <= end for start, end in _HANGUL_RANGES):
            hangul += 1
        elif _CJK_RANGE[0] <= cp <= _CJK_RANGE[1]:
            cjk += 1
        elif any(start <= cp <= end for start, end in _LATIN_RANGES):
            latin += 1

    return {
        'hangul': hangul,
        'cjk': cjk,
        'latin': latin,
        'total_alpha': hangul + cjk + latin,
    }


def _collect_all_text(layout_dets: list[dict[str, Any]]) -> str:
    """Collect all text content from layout elements.

    Joins text from text, html (stripped), and latex fields.

    Args:
        layout_dets: List of layout element dicts.

    Returns:
        Combined text string.
    """
    parts: list[str] = []
    for el in layout_dets:
        text = el.get('text', '')
        if text:
            parts.append(text)
        html = el.get('html', '')
        if html:
            parts.append(_strip_html_tags(html))
        latex = el.get('latex', '')
        if latex:
            parts.append(latex)
    return ' '.join(parts)


def _strip_html_tags(html: str) -> str:
    """Strip HTML tags from a string, returning text content only.

    Args:
        html: HTML string.

    Returns:
        Text with HTML tags removed.
    """
    return re.sub(r'<[^>]+>', ' ', html)
