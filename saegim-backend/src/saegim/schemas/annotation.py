"""OmniDocBench annotation data schemas."""

from typing import Any

from pydantic import BaseModel, Field


class SpanElement(BaseModel):
    """Span-level element within a block."""

    category_type: str = Field(description='Span category: text_span, equation_inline, etc.')
    poly: list[float] = Field(description='Bounding box polygon [x1,y1,...,x4,y4]')
    ignore: bool = Field(default=False)
    text: str = Field(default='')


class LayoutElement(BaseModel):
    """Block-level layout element in OmniDocBench format."""

    category_type: str = Field(description='Block category: title, text_block, table, etc.')
    poly: list[float] = Field(description='Bounding box polygon [x1,y1,...,x4,y4]')
    ignore: bool = Field(default=False)
    order: int = Field(default=0, description='Reading order')
    anno_id: int = Field(description='Unique annotation ID within the page')
    text: str = Field(default='')
    latex: str = Field(default='')
    html: str = Field(default='')
    attribute: dict[str, Any] = Field(default_factory=dict)
    line_with_spans: list[SpanElement] = Field(default_factory=list)
    merge_list: list[dict[str, Any]] = Field(default_factory=list)


class Relation(BaseModel):
    """Relation between two elements."""

    source_anno_id: int
    target_anno_id: int
    relation_type: str = Field(default='parent_son')


class PageAttribute(BaseModel):
    """Page-level attribute labels."""

    data_source: str = Field(default='')
    language: str = Field(default='')
    layout: str = Field(default='')
    watermark: bool = Field(default=False)
    fuzzy_scan: bool = Field(default=False)
    colorful_background: bool = Field(default=False)


class AnnotationData(BaseModel):
    """Complete annotation data for a single page (OmniDocBench format)."""

    layout_dets: list[LayoutElement] = Field(default_factory=list)
    page_attribute: PageAttribute = Field(default_factory=PageAttribute)
    extra: dict[str, Any] = Field(default_factory=lambda: {'relation': []})
