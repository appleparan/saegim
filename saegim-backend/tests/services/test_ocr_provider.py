"""Tests for OCR provider utilities and prompts."""

from saegim.services.ocr_provider import get_text_prompt


class TestGetTextPrompt:
    def test_default_prompt(self):
        prompt = get_text_prompt()
        assert 'Read all text' in prompt

    def test_table_prompt(self):
        prompt = get_text_prompt('table')
        assert 'markdown table' in prompt

    def test_equation_prompt(self):
        prompt = get_text_prompt('equation_isolated')
        assert 'LaTeX' in prompt

    def test_code_prompt(self):
        prompt = get_text_prompt('code_txt')
        assert 'source code' in prompt

    def test_unknown_category_returns_default(self):
        prompt = get_text_prompt('figure')
        assert 'Read all text' in prompt
