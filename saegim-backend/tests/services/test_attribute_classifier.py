"""Tests for auto attribute classifier."""

from saegim.services.attribute_classifier import (
    _classify_data_source,
    _classify_element_attributes,
    _classify_equation_attributes,
    _classify_equation_language,
    _classify_page_language,
    _classify_page_layout,
    _classify_table_attributes,
    _classify_table_language,
    _classify_table_layout,
    _classify_text_attributes,
    _classify_text_language,
    _collect_all_text,
    _count_column_clusters,
    _count_unicode_ranges,
    _detect_equation_in_table,
    _detect_table_span,
    _detect_table_vertical,
    _strip_html_tags,
    classify_attributes,
)

# ============================================================
# Shared helpers
# ============================================================


class TestCountUnicodeRanges:
    def test_pure_hangul(self):
        result = _count_unicode_ranges('안녕하세요')
        assert result['hangul'] == 5
        assert result['latin'] == 0
        assert result['cjk'] == 0
        assert result['total_alpha'] == 5

    def test_pure_english(self):
        result = _count_unicode_ranges('Hello')
        assert result['latin'] == 5
        assert result['hangul'] == 0
        assert result['cjk'] == 0

    def test_mixed_korean_english(self):
        result = _count_unicode_ranges('Hello 안녕')
        assert result['latin'] == 5
        assert result['hangul'] == 2
        assert result['total_alpha'] == 7

    def test_chinese_characters(self):
        result = _count_unicode_ranges('中文')
        assert result['cjk'] == 2
        assert result['hangul'] == 0
        assert result['latin'] == 0

    def test_empty_string(self):
        result = _count_unicode_ranges('')
        assert result['total_alpha'] == 0
        assert result['hangul'] == 0
        assert result['latin'] == 0
        assert result['cjk'] == 0

    def test_numbers_and_punctuation_not_counted(self):
        result = _count_unicode_ranges('123!@# .,;:')
        assert result['total_alpha'] == 0

    def test_hangul_jamo(self):
        # ㄱ (U+3131), ㅎ (U+314E) are Hangul Compatibility Jamo
        result = _count_unicode_ranges('ㄱㅎ')
        assert result['hangul'] == 2

    def test_latin_extended(self):
        # é (U+00E9), ñ (U+00F1) are Latin Extended
        result = _count_unicode_ranges('éñ')
        assert result['latin'] == 2


class TestStripHtmlTags:
    def test_simple_tags(self):
        assert _strip_html_tags('<b>bold</b>').strip() == 'bold'

    def test_table_html(self):
        html = '<table><tr><td>A</td><td>B</td></tr></table>'
        result = _strip_html_tags(html)
        assert 'A' in result
        assert 'B' in result
        assert '<' not in result

    def test_empty_string(self):
        assert _strip_html_tags('') == ''

    def test_no_tags(self):
        assert _strip_html_tags('plain text') == 'plain text'


class TestCollectAllText:
    def test_collects_text_fields(self):
        elements = [
            {'text': 'first', 'html': '', 'latex': ''},
            {'text': 'second', 'html': '', 'latex': ''},
        ]
        result = _collect_all_text(elements)
        assert 'first' in result
        assert 'second' in result

    def test_collects_html_stripped(self):
        elements = [{'text': '', 'html': '<td>table data</td>', 'latex': ''}]
        result = _collect_all_text(elements)
        assert 'table data' in result
        assert '<td>' not in result

    def test_collects_latex(self):
        elements = [{'text': '', 'html': '', 'latex': 'E = mc^2'}]
        result = _collect_all_text(elements)
        assert 'E = mc^2' in result

    def test_empty_elements(self):
        assert _collect_all_text([]) == ''

    def test_elements_without_fields(self):
        elements = [{'category_type': 'figure'}]
        result = _collect_all_text(elements)
        assert result == ''


# ============================================================
# Page-level classification
# ============================================================


class TestClassifyPageLanguage:
    def test_korean_dominant(self):
        elements = [
            {
                'category_type': 'text_block',
                'text': '이것은 한국어 문서입니다 자연어 처리 기술을 사용합니다',
            }
        ]
        assert _classify_page_language(elements) == 'ko'

    def test_english_dominant(self):
        elements = [
            {
                'category_type': 'text_block',
                'text': 'This is an English document about natural language processing technology',
            }
        ]
        assert _classify_page_language(elements) == 'en'

    def test_mixed_korean_english(self):
        elements = [
            {
                'category_type': 'text_block',
                'text': '이것은 mixed document 입니다 NLP 기술을 testing 합니다 여러 단어',
            }
        ]
        result = _classify_page_language(elements)
        assert result == 'ko_en_mixed'

    def test_mixed_korean_chinese(self):
        elements = [{'category_type': 'text_block', 'text': '한국 中文混合漢字文書韓國語中國語'}]
        result = _classify_page_language(elements)
        assert result == 'ko_ch_mixed'

    def test_empty_elements(self):
        assert _classify_page_language([]) == ''

    def test_insufficient_text(self):
        elements = [{'category_type': 'text_block', 'text': 'Hi'}]
        assert _classify_page_language(elements) == ''

    def test_multiple_elements(self):
        elements = [
            {'category_type': 'text_block', 'text': '한국어 텍스트 블록'},
            {'category_type': 'title', 'text': '제목입니다 한국어'},
            {'category_type': 'figure', 'text': ''},
        ]
        assert _classify_page_language(elements) == 'ko'


class TestClassifyPageLayout:
    def test_single_column_full_width(self):
        elements = [
            {'category_type': 'text_block', 'poly': [100, 0, 900, 0, 900, 100, 100, 100]},
            {'category_type': 'text_block', 'poly': [100, 110, 900, 110, 900, 200, 100, 200]},
        ]
        assert _classify_page_layout(elements) == 'single_column'

    def test_double_column(self):
        elements = [
            {'category_type': 'text_block', 'poly': [50, 0, 450, 0, 450, 100, 50, 100]},
            {'category_type': 'text_block', 'poly': [50, 110, 450, 110, 450, 200, 50, 200]},
            {'category_type': 'text_block', 'poly': [550, 0, 950, 0, 950, 100, 550, 100]},
            {'category_type': 'text_block', 'poly': [550, 110, 950, 110, 950, 200, 550, 200]},
        ]
        assert _classify_page_layout(elements) == 'double_column'

    def test_three_column(self):
        elements = [
            {'category_type': 'text_block', 'poly': [50, 0, 280, 0, 280, 100, 50, 100]},
            {'category_type': 'text_block', 'poly': [350, 0, 580, 0, 580, 100, 350, 100]},
            {'category_type': 'text_block', 'poly': [650, 0, 880, 0, 880, 100, 650, 100]},
        ]
        assert _classify_page_layout(elements) == 'three_column'

    def test_1andmore_column(self):
        # Full-width title + two-column body
        elements = [
            {'category_type': 'title', 'poly': [50, 0, 950, 0, 950, 50, 50, 50]},
            {'category_type': 'text_block', 'poly': [50, 100, 450, 100, 450, 300, 50, 300]},
            {'category_type': 'text_block', 'poly': [550, 100, 950, 100, 950, 300, 550, 300]},
        ]
        assert _classify_page_layout(elements) == '1andmore_column'

    def test_few_elements_defaults_to_single(self):
        elements = [{'category_type': 'text_block', 'poly': [100, 0, 500, 0, 500, 100, 100, 100]}]
        assert _classify_page_layout(elements) == 'single_column'

    def test_no_text_elements(self):
        elements = [{'category_type': 'figure', 'poly': [0, 0, 1000, 0, 1000, 1000, 0, 1000]}]
        assert _classify_page_layout(elements) == 'single_column'

    def test_empty_elements(self):
        assert _classify_page_layout([]) == 'single_column'

    def test_elements_without_poly(self):
        elements = [
            {'category_type': 'text_block'},
            {'category_type': 'text_block'},
        ]
        assert _classify_page_layout(elements) == 'single_column'


class TestCountColumnClusters:
    def test_single_cluster(self):
        assert _count_column_clusters([100, 110, 120], page_width=1000, _page_left=0) == 1

    def test_two_clusters(self):
        assert _count_column_clusters([100, 110, 600, 610], page_width=1000, _page_left=0) == 2

    def test_three_clusters(self):
        assert (
            _count_column_clusters([100, 110, 400, 410, 700, 710], page_width=1000, _page_left=0)
            == 3
        )

    def test_empty_list(self):
        assert _count_column_clusters([], page_width=1000, _page_left=0) == 0

    def test_single_element(self):
        assert _count_column_clusters([500], page_width=1000, _page_left=0) == 1


class TestClassifyDataSource:
    def test_academic_literature_english(self):
        elements = [
            {'text': 'Abstract. This paper presents a novel approach to...'},
            {'text': 'References\n[1] Smith et al.'},
        ]
        assert _classify_data_source(elements) == 'academic_literature'

    def test_academic_literature_korean(self):
        elements = [{'text': '초록: 본 연구는 한국어 문서 처리를 다룬다'}]
        assert _classify_data_source(elements) == 'academic_literature'

    def test_academic_with_doi(self):
        elements = [{'text': 'DOI: 10.1234/test.2024'}]
        assert _classify_data_source(elements) == 'academic_literature'

    def test_exam_paper(self):
        elements = [{'text': '2024학년도 대학 수능 시험 문제지'}]
        assert _classify_data_source(elements) == 'exam_paper'

    def test_government_doc(self):
        elements = [{'text': '국토교통부 공문 시행일: 2024.01.01'}]
        assert _classify_data_source(elements) == 'government_doc'

    def test_financial_report(self):
        elements = [{'text': '제50기 감사보고서 연결재무제표'}]
        assert _classify_data_source(elements) == 'financial_report_kr'

    def test_book(self):
        elements = [{'text': 'Chapter 1: Getting Started with Data'}]
        assert _classify_data_source(elements) == 'book'

    def test_book_korean(self):
        elements = [{'text': '제 3 장 데이터 전처리'}]
        assert _classify_data_source(elements) == 'book'

    def test_newspaper(self):
        elements = [{'text': '홍길동 기자'}]
        assert _classify_data_source(elements) == 'newspaper'

    def test_ppt(self):
        elements = [{'text': 'Slide 1: Project Overview'}]
        assert _classify_data_source(elements) == 'PPT2PDF'

    def test_no_match_returns_empty(self):
        elements = [{'text': '일반적인 내용의 문서입니다'}]
        assert _classify_data_source(elements) == ''

    def test_empty_elements(self):
        assert _classify_data_source([]) == ''

    def test_priority_academic_over_book(self):
        # If both patterns match, academic should win (higher priority)
        elements = [{'text': 'Abstract Chapter 1 Introduction References'}]
        assert _classify_data_source(elements) == 'academic_literature'


# ============================================================
# Element-level classification
# ============================================================


class TestClassifyTextLanguage:
    def test_korean(self):
        assert _classify_text_language('한국어 텍스트 블록입니다 여러 글자') == 'text_ko'

    def test_english(self):
        assert _classify_text_language('English text block content here') == 'text_en'

    def test_mixed(self):
        result = _classify_text_language('한국어 English mixed 텍스트 content 입니다')
        assert result == 'text_ko_en_mixed'

    def test_insufficient_text(self):
        assert _classify_text_language('Hi') == ''

    def test_empty(self):
        assert _classify_text_language('') == ''


class TestClassifyTextAttributes:
    def test_korean_text_block(self):
        element = {
            'category_type': 'text_block',
            'text': '한국어 텍스트 블록입니다 여러 글자가 있습니다',
        }
        attrs = _classify_text_attributes(element)
        assert attrs['text_language'] == 'text_ko'
        assert attrs['text_background'] == 'white'
        assert attrs['text_rotate'] == 'normal'

    def test_english_title(self):
        element = {
            'category_type': 'title',
            'text': 'Introduction to Machine Learning Systems',
        }
        attrs = _classify_text_attributes(element)
        assert attrs['text_language'] == 'text_en'

    def test_empty_text(self):
        element = {'category_type': 'text_block', 'text': ''}
        attrs = _classify_text_attributes(element)
        assert attrs['text_language'] == ''
        assert attrs['text_background'] == 'white'
        assert attrs['text_rotate'] == 'normal'


class TestClassifyTableLayout:
    def test_horizontal_table(self):
        # wider than tall
        poly = [0, 0, 500, 0, 500, 300, 0, 300]
        assert _classify_table_layout(poly) == 'horizontal'

    def test_vertical_table(self):
        # taller than wide (height > 1.5x width)
        poly = [0, 0, 100, 0, 100, 500, 0, 500]
        assert _classify_table_layout(poly) == 'vertical'

    def test_square_table(self):
        poly = [0, 0, 100, 0, 100, 100, 0, 100]
        assert _classify_table_layout(poly) == 'horizontal'

    def test_empty_poly(self):
        assert _classify_table_layout([]) == 'horizontal'

    def test_short_poly(self):
        assert _classify_table_layout([0, 0, 100]) == 'horizontal'


class TestDetectTableSpan:
    def test_with_colspan(self):
        html = '<table><tr><td colspan="2">Header</td></tr></table>'
        assert _detect_table_span(html) is True

    def test_with_rowspan(self):
        html = '<table><tr><td rowspan="3">Side</td></tr></table>'
        assert _detect_table_span(html) is True

    def test_colspan_single_quotes(self):
        html = "<table><tr><td colspan='2'>Header</td></tr></table>"
        assert _detect_table_span(html) is True

    def test_colspan_no_quotes(self):
        html = '<table><tr><td colspan=2>Header</td></tr></table>'
        assert _detect_table_span(html) is True

    def test_without_span(self):
        html = '<table><tr><td>A</td><td>B</td></tr></table>'
        assert _detect_table_span(html) is False

    def test_empty_html(self):
        assert _detect_table_span('') is False


class TestClassifyTableLanguage:
    def test_korean_table(self):
        element = {
            'text': '',
            'html': (
                '<table><tr><td>이름</td><td>나이</td><td>주소</td><td>연락처</td></tr></table>'
            ),
        }
        assert _classify_table_language(element) == 'table_ko'

    def test_english_table(self):
        element = {
            'text': '',
            'html': '<table><tr><td>Name</td><td>Score</td></tr></table>',
        }
        assert _classify_table_language(element) == 'table_en'

    def test_mixed_table(self):
        element = {
            'text': '',
            'html': '<table><tr><td>이름 Name</td><td>점수 Score</td></tr></table>',
        }
        assert _classify_table_language(element) == 'table_ko_en_mixed'

    def test_empty_content(self):
        element = {'text': '', 'html': ''}
        assert _classify_table_language(element) == ''


class TestDetectEquationInTable:
    def test_latex_frac(self):
        element = {'text': '', 'html': '<td>\\frac{1}{2}</td>', 'latex': ''}
        assert _detect_equation_in_table(element) is True

    def test_latex_sum(self):
        element = {'text': '\\sum_{i=1}^{n}', 'html': '', 'latex': ''}
        assert _detect_equation_in_table(element) is True

    def test_inline_math(self):
        element = {'text': 'Value is $x^2$', 'html': '', 'latex': ''}
        assert _detect_equation_in_table(element) is True

    def test_no_equation(self):
        element = {'text': 'plain text data', 'html': '<td>data</td>', 'latex': ''}
        assert _detect_equation_in_table(element) is False

    def test_empty_element(self):
        element = {'text': '', 'html': '', 'latex': ''}
        assert _detect_equation_in_table(element) is False

    def test_latex_in_latex_field(self):
        element = {'text': '', 'html': '', 'latex': '\\sqrt{2}'}
        assert _detect_equation_in_table(element) is True


class TestDetectTableVertical:
    def test_vertical(self):
        # height (500) > width (100) * 2
        poly = [0, 0, 100, 0, 100, 500, 0, 500]
        assert _detect_table_vertical(poly) is True

    def test_not_vertical(self):
        poly = [0, 0, 500, 0, 500, 300, 0, 300]
        assert _detect_table_vertical(poly) is False

    def test_borderline_not_vertical(self):
        # height (200) == width (100) * 2, not strictly greater
        poly = [0, 0, 100, 0, 100, 200, 0, 200]
        assert _detect_table_vertical(poly) is False

    def test_empty_poly(self):
        assert _detect_table_vertical([]) is False


class TestClassifyTableAttributes:
    def test_full_table_classification(self):
        element = {
            'category_type': 'table',
            'text': '',
            'html': '<table><tr><td colspan="2">\\frac{a}{b}</td></tr></table>',
            'latex': '',
            'poly': [0, 0, 500, 0, 500, 300, 0, 300],
        }
        attrs = _classify_table_attributes(element)
        assert attrs['with_span'] is True
        assert attrs['include_equation'] is True
        assert attrs['table_layout'] == 'horizontal'
        assert attrs['table_vertical'] is False
        assert attrs['include_background'] is False
        assert attrs['line'] == ''

    def test_vertical_table(self):
        element = {
            'category_type': 'table',
            'text': '',
            'html': '<table><tr><td>data</td></tr></table>',
            'latex': '',
            'poly': [0, 0, 100, 0, 100, 500, 0, 500],
        }
        attrs = _classify_table_attributes(element)
        assert attrs['table_vertical'] is True
        assert attrs['table_layout'] == 'vertical'


class TestClassifyEquationLanguage:
    def test_english_equation(self):
        element = {'latex': 'E = mc^2', 'text': ''}
        assert _classify_equation_language(element) == 'equation_en'

    def test_korean_equation(self):
        element = {'latex': '속도 = \\frac{거리}{시간}', 'text': ''}
        assert _classify_equation_language(element) == 'equation_ko'

    def test_korean_in_text_field(self):
        element = {'latex': '', 'text': '속도 공식'}
        assert _classify_equation_language(element) == 'equation_ko'

    def test_empty_fields(self):
        element = {'latex': '', 'text': ''}
        assert _classify_equation_language(element) == 'equation_en'


class TestClassifyEquationAttributes:
    def test_english_equation(self):
        element = {'category_type': 'equation_isolated', 'latex': 'E = mc^2', 'text': ''}
        attrs = _classify_equation_attributes(element)
        assert attrs['formula_type'] == 'print'
        assert attrs['equation_language'] == 'equation_en'

    def test_korean_equation(self):
        element = {
            'category_type': 'equation_isolated',
            'latex': '속도 = \\frac{거리}{시간}',
            'text': '',
        }
        attrs = _classify_equation_attributes(element)
        assert attrs['formula_type'] == 'print'
        assert attrs['equation_language'] == 'equation_ko'


class TestClassifyElementAttributes:
    def test_text_block(self):
        element = {'category_type': 'text_block', 'text': '한국어 텍스트입니다 여러 글자'}
        attrs = _classify_element_attributes(element)
        assert 'text_language' in attrs
        assert 'text_background' in attrs

    def test_title(self):
        element = {'category_type': 'title', 'text': 'English Title Here Content'}
        attrs = _classify_element_attributes(element)
        assert attrs['text_language'] == 'text_en'

    def test_table(self):
        element = {
            'category_type': 'table',
            'text': '',
            'html': '<table><tr><td>A</td></tr></table>',
            'latex': '',
            'poly': [0, 0, 100, 0, 100, 100, 0, 100],
        }
        attrs = _classify_element_attributes(element)
        assert 'with_span' in attrs
        assert 'table_layout' in attrs

    def test_equation(self):
        element = {'category_type': 'equation_isolated', 'latex': 'x^2', 'text': ''}
        attrs = _classify_element_attributes(element)
        assert attrs['formula_type'] == 'print'
        assert attrs['equation_language'] == 'equation_en'

    def test_figure_returns_empty(self):
        element = {'category_type': 'figure'}
        assert _classify_element_attributes(element) == {}

    def test_unknown_category_returns_empty(self):
        element = {'category_type': 'header'}
        assert _classify_element_attributes(element) == {}


# ============================================================
# Integration: classify_attributes
# ============================================================


class TestClassifyAttributes:
    def test_populates_page_attribute(self):
        extracted = {
            'layout_dets': [
                {
                    'category_type': 'text_block',
                    'poly': [100, 0, 900, 0, 900, 100, 100, 100],
                    'text': '이것은 한국어 학술 논문입니다 Abstract 초록 참고문헌 References',
                },
            ],
            'page_attribute': {},
            'extra': {'relation': []},
        }
        result = classify_attributes(extracted)
        assert result['page_attribute']['language'] != ''
        assert result['page_attribute']['layout'] == 'single_column'
        assert result['page_attribute']['data_source'] == 'academic_literature'
        assert result['page_attribute']['watermark'] is False
        assert result['page_attribute']['fuzzy_scan'] is False
        assert result['page_attribute']['colorful_background'] is False

    def test_populates_element_attributes(self):
        extracted = {
            'layout_dets': [
                {
                    'category_type': 'text_block',
                    'poly': [100, 0, 900, 0, 900, 100, 100, 100],
                    'text': 'English text content here for testing only purposes',
                    'attribute': {},
                },
                {
                    'category_type': 'table',
                    'poly': [100, 200, 900, 200, 900, 500, 100, 500],
                    'html': '<table><tr><td>A</td></tr></table>',
                    'text': '',
                    'latex': '',
                    'attribute': {},
                },
            ],
            'page_attribute': {},
            'extra': {'relation': []},
        }
        result = classify_attributes(extracted)

        text_elem = result['layout_dets'][0]
        assert text_elem['attribute']['text_language'] == 'text_en'
        assert text_elem['attribute']['text_background'] == 'white'

        table_elem = result['layout_dets'][1]
        assert table_elem['attribute']['with_span'] is False
        assert table_elem['attribute']['table_layout'] == 'horizontal'

    def test_handles_empty_layout_dets(self):
        extracted = {
            'layout_dets': [],
            'page_attribute': {},
            'extra': {'relation': []},
        }
        result = classify_attributes(extracted)
        assert result['page_attribute']['watermark'] is False
        assert result['page_attribute']['language'] == ''
        assert result['layout_dets'] == []

    def test_preserves_extra_field(self):
        extracted = {
            'layout_dets': [],
            'page_attribute': {},
            'extra': {'relation': [{'source_anno_id': 0, 'target_anno_id': 1}]},
        }
        result = classify_attributes(extracted)
        assert result['extra'] == {'relation': [{'source_anno_id': 0, 'target_anno_id': 1}]}

    def test_fill_missing_preserves_existing_element_attributes(self):
        extracted = {
            'layout_dets': [
                {
                    'category_type': 'text_block',
                    'poly': [100, 0, 900, 0, 900, 100, 100, 100],
                    'text': 'Hello world content text here for testing',
                    'attribute': {'text_language': 'text_ko'},
                },
            ],
            'page_attribute': {},
            'extra': {'relation': []},
        }
        result = classify_attributes(extracted)
        # Pre-existing value should be preserved
        assert result['layout_dets'][0]['attribute']['text_language'] == 'text_ko'
        # Missing fields should be filled
        assert result['layout_dets'][0]['attribute']['text_background'] == 'white'

    def test_fill_missing_preserves_existing_page_attributes(self):
        extracted = {
            'layout_dets': [
                {
                    'category_type': 'text_block',
                    'poly': [100, 0, 900, 0, 900, 100, 100, 100],
                    'text': '한국어 텍스트 내용입니다 여러 글자',
                },
            ],
            'page_attribute': {'language': 'en'},
            'extra': {'relation': []},
        }
        result = classify_attributes(extracted)
        # Pre-existing value should be preserved
        assert result['page_attribute']['language'] == 'en'
        # Missing fields should be filled
        assert result['page_attribute']['layout'] == 'single_column'

    def test_fills_empty_string_attribute(self):
        extracted = {
            'layout_dets': [
                {
                    'category_type': 'text_block',
                    'poly': [100, 0, 900, 0, 900, 100, 100, 100],
                    'text': '한국어 텍스트 내용입니다 여러 글자',
                    'attribute': {'text_language': ''},
                },
            ],
            'page_attribute': {},
            'extra': {'relation': []},
        }
        result = classify_attributes(extracted)
        # Empty string should be overwritten
        assert result['layout_dets'][0]['attribute']['text_language'] == 'text_ko'

    def test_handles_none_page_attribute(self):
        extracted = {
            'layout_dets': [],
            'page_attribute': None,
            'extra': {'relation': []},
        }
        result = classify_attributes(extracted)
        assert result['page_attribute']['watermark'] is False

    def test_handles_none_element_attribute(self):
        extracted = {
            'layout_dets': [
                {
                    'category_type': 'text_block',
                    'poly': [100, 0, 900, 0, 900, 100, 100, 100],
                    'text': '한국어 텍스트 블록입니다 여러 글자',
                    'attribute': None,
                },
            ],
            'page_attribute': {},
            'extra': {'relation': []},
        }
        result = classify_attributes(extracted)
        assert result['layout_dets'][0]['attribute']['text_language'] == 'text_ko'

    def test_elements_without_attribute_key(self):
        extracted = {
            'layout_dets': [
                {
                    'category_type': 'equation_isolated',
                    'poly': [100, 0, 300, 0, 300, 50, 100, 50],
                    'latex': 'E = mc^2',
                    'text': '',
                },
            ],
            'page_attribute': {},
            'extra': {'relation': []},
        }
        result = classify_attributes(extracted)
        assert result['layout_dets'][0]['attribute']['formula_type'] == 'print'
        assert result['layout_dets'][0]['attribute']['equation_language'] == 'equation_en'
