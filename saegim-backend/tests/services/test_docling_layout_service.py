"""Tests for Docling layout detection service."""

import pytest

from saegim.services.docling_layout_service import (
    _extract_locs,
    _otsl_to_html,
    _scale_bbox,
    parse_doctags_to_regions,
)


class TestExtractLocs:
    def test_valid_4_locs(self):
        result = _extract_locs('<loc_10><loc_20><loc_300><loc_400>')
        assert result == (10, 20, 300, 400)

    def test_too_few_locs_raises(self):
        with pytest.raises(ValueError, match='Expected 4 loc values'):
            _extract_locs('<loc_10><loc_20>')

    def test_no_locs_raises(self):
        with pytest.raises(ValueError, match='Expected 4 loc values'):
            _extract_locs('')


class TestScaleBbox:
    def test_identity_at_500(self):
        result = _scale_bbox(0, 0, 500, 500, 500, 500)
        assert result == (0.0, 0.0, 500.0, 500.0)

    def test_scale_to_1000x2000(self):
        result = _scale_bbox(0, 0, 250, 250, 1000, 2000)
        assert result == (0.0, 0.0, 500.0, 1000.0)

    def test_arbitrary_coords(self):
        result = _scale_bbox(100, 200, 300, 400, 1000, 1000)
        assert result == (200.0, 400.0, 600.0, 800.0)

    def test_zero_page_dims_raises(self):
        with pytest.raises(ValueError, match='Page dimensions must be positive'):
            _scale_bbox(0, 0, 100, 100, 0, 500)


class TestOtslToHtml:
    def test_empty_content(self):
        assert _otsl_to_html('') == '<table></table>'

    def test_single_cell(self):
        result = _otsl_to_html('<otsl><fcel>Hello<nl></otsl>')
        assert '<td>Hello</td>' in result
        assert '<table>' in result

    def test_multiple_cells(self):
        result = _otsl_to_html('<fcel>A<fcel>B<nl><fcel>C<fcel>D<nl>')
        assert result.count('<td>') == 4
        assert '<tr>' in result

    def test_empty_cell(self):
        result = _otsl_to_html('<fcel>A<ecel><nl>')
        assert '<td>A</td>' in result
        assert '<td></td>' in result

    def test_colspan_with_lcel(self):
        result = _otsl_to_html('<fcel>Wide<lcel><nl>')
        assert 'colspan="2"' in result


class TestParseDoctags:
    def test_single_text_block(self):
        doctags = '<text><loc_10><loc_20><loc_300><loc_400>Hello world</text>'
        regions = parse_doctags_to_regions(doctags, 1000, 1000)

        assert len(regions) == 1
        assert regions[0].category == 'text_block'
        assert regions[0].text == 'Hello world'
        assert regions[0].score == 1.0
        assert regions[0].bbox == (20.0, 40.0, 600.0, 800.0)

    def test_title(self):
        doctags = '<title><loc_10><loc_5><loc_200><loc_30>Chapter 1</title>'
        regions = parse_doctags_to_regions(doctags, 500, 500)

        assert len(regions) == 1
        assert regions[0].category == 'title'
        assert regions[0].text == 'Chapter 1'

    def test_table_produces_html(self):
        doctags = '<table><loc_0><loc_0><loc_499><loc_499><otsl><fcel>Cell</otsl></table>'
        regions = parse_doctags_to_regions(doctags, 500, 500)

        assert len(regions) == 1
        assert regions[0].category == 'table'
        assert '<table>' in regions[0].text
        assert '<td>Cell</td>' in regions[0].text

    def test_figure_no_text(self):
        doctags = '<picture><loc_0><loc_0><loc_100><loc_100>fig caption</picture>'
        regions = parse_doctags_to_regions(doctags, 500, 500)

        assert len(regions) == 1
        assert regions[0].category == 'figure'
        assert regions[0].text is None

    def test_formula(self):
        doctags = '<formula><loc_10><loc_10><loc_200><loc_50>E=mc^2</formula>'
        regions = parse_doctags_to_regions(doctags, 500, 500)

        assert len(regions) == 1
        assert regions[0].category == 'equation'
        assert regions[0].text == 'E=mc^2'

    def test_multiple_elements(self):
        doctags = (
            '<title><loc_10><loc_5><loc_490><loc_30>Title</title>'
            '<text><loc_10><loc_50><loc_490><loc_200>Body text</text>'
            '<picture><loc_10><loc_220><loc_490><loc_400>img</picture>'
        )
        regions = parse_doctags_to_regions(doctags, 1000, 1000)

        assert len(regions) == 3
        assert regions[0].category == 'title'
        assert regions[1].category == 'text_block'
        assert regions[2].category == 'figure'

    def test_empty_doctags(self):
        regions = parse_doctags_to_regions('', 500, 500)
        assert regions == []

    def test_unknown_tag_ignored(self):
        doctags = '<unknown><loc_0><loc_0><loc_100><loc_100>data</unknown>'
        regions = parse_doctags_to_regions(doctags, 500, 500)
        assert regions == []
