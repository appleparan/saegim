import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/svelte'
import { annotationStore } from '$lib/stores/annotation.svelte'
import TextOverlay from '$lib/components/canvas/TextOverlay.svelte'
import { canvasStore } from '$lib/stores/canvas.svelte'
import type { AnnotationData } from '$lib/types/omnidocbench'

function makeAnnotationData(elements: AnnotationData['layout_dets']): AnnotationData {
  return {
    layout_dets: elements,
    page_attribute: {},
    extra: { relation: [] },
  }
}

describe('TextOverlay', () => {
  afterEach(() => {
    cleanup()
  })

  beforeEach(() => {
    annotationStore.clear()
    canvasStore.setImageDimensions(800, 1100)
    canvasStore.setScale(1)
    canvasStore.setOffset(0, 0)
  })

  it('renders text blocks as transparent text divs', () => {
    annotationStore.load(
      'test-page',
      makeAnnotationData([
        {
          category_type: 'text_block',
          poly: [10, 10, 200, 10, 200, 40, 10, 40],
          ignore: false,
          order: 0,
          anno_id: 0,
          text: '안녕하세요 테스트',
        },
        {
          category_type: 'title',
          poly: [10, 50, 300, 50, 300, 80, 10, 80],
          ignore: false,
          order: 1,
          anno_id: 1,
          text: '제목입니다',
        },
      ]),
    )

    render(TextOverlay, { props: { pointerEvents: 'auto' } })

    // Both text blocks should be rendered
    expect(screen.getByText('안녕하세요 테스트')).toBeTruthy()
    expect(screen.getByText('제목입니다')).toBeTruthy()
  })

  it('excludes image-block categories (figure, table, equation_isolated)', () => {
    annotationStore.load(
      'test-page',
      makeAnnotationData([
        {
          category_type: 'text_block',
          poly: [10, 10, 200, 10, 200, 40, 10, 40],
          ignore: false,
          order: 0,
          anno_id: 0,
          text: '표시될 텍스트',
        },
        {
          category_type: 'figure',
          poly: [50, 300, 450, 300, 450, 600, 50, 600],
          ignore: false,
          order: 1,
          anno_id: 1,
          text: '숨겨질 그림',
        },
        {
          category_type: 'table',
          poly: [50, 700, 450, 700, 450, 900, 50, 900],
          ignore: false,
          order: 2,
          anno_id: 2,
          text: '숨겨질 테이블',
        },
      ]),
    )

    render(TextOverlay, { props: { pointerEvents: 'auto' } })

    expect(screen.getByText('표시될 텍스트')).toBeTruthy()
    expect(screen.queryByText('숨겨질 그림')).toBeNull()
    expect(screen.queryByText('숨겨질 테이블')).toBeNull()
  })

  it('renders empty string when text is undefined', () => {
    annotationStore.load(
      'test-page',
      makeAnnotationData([
        {
          category_type: 'header',
          poly: [10, 10, 200, 10, 200, 30, 10, 30],
          ignore: false,
          order: 0,
          anno_id: 0,
        },
      ]),
    )

    render(TextOverlay, { props: { pointerEvents: 'auto' } })

    // Should render a div with role="textbox" even without text
    const textboxes = screen.getAllByRole('textbox')
    expect(textboxes).toHaveLength(1)
    expect(textboxes[0].textContent).toBe('')
  })

  it('respects pointerEvents prop', () => {
    annotationStore.load(
      'test-page',
      makeAnnotationData([
        {
          category_type: 'text_block',
          poly: [10, 10, 200, 10, 200, 40, 10, 40],
          ignore: false,
          order: 0,
          anno_id: 0,
          text: '텍스트',
        },
      ]),
    )

    const { container } = render(TextOverlay, {
      props: { pointerEvents: 'none' },
    })

    const overlayDiv = container.querySelector('[style*="z-index: 20"]')
    expect(overlayDiv).toBeTruthy()
    expect((overlayDiv as HTMLElement).style.pointerEvents).toBe('none')
  })

  it('positions text divs using poly coordinates', () => {
    annotationStore.load(
      'test-page',
      makeAnnotationData([
        {
          category_type: 'text_block',
          poly: [100, 200, 500, 200, 500, 240, 100, 240],
          ignore: false,
          order: 0,
          anno_id: 0,
          text: '위치 테스트',
        },
      ]),
    )

    render(TextOverlay, { props: { pointerEvents: 'auto' } })

    const textDiv = screen.getByText('위치 테스트')
    const style = textDiv.style
    expect(style.left).toBe('100px')
    expect(style.top).toBe('200px')
    expect(style.width).toBe('400px')
    expect(style.height).toBe('40px')
  })

  it('renders all text-category types', () => {
    const textCategories = [
      'title',
      'text_block',
      'header',
      'footer',
      'page_number',
      'page_footnote',
      'figure_caption',
      'figure_footnote',
      'table_caption',
      'table_footnote',
      'equation_caption',
      'code_txt',
      'code_txt_caption',
      'reference',
      'abandon',
    ] as const

    annotationStore.load(
      'test-page',
      makeAnnotationData(
        textCategories.map((cat, i) => ({
          category_type: cat,
          poly: [10, i * 30, 200, i * 30, 200, i * 30 + 20, 10, i * 30 + 20] as const,
          ignore: false,
          order: i,
          anno_id: i,
          text: `text-${cat}`,
        })),
      ),
    )

    render(TextOverlay, { props: { pointerEvents: 'auto' } })

    for (const cat of textCategories) {
      expect(screen.getByText(`text-${cat}`)).toBeTruthy()
    }
  })

  it('renders nothing when no elements exist', () => {
    annotationStore.load('test-page', makeAnnotationData([]))

    const { container } = render(TextOverlay, {
      props: { pointerEvents: 'auto' },
    })

    const textboxes = container.querySelectorAll('[role="textbox"]')
    expect(textboxes).toHaveLength(0)
  })

  it('applies CSS transform from canvasStore for zoom/pan sync', () => {
    canvasStore.setScale(2)
    canvasStore.setOffset(50, 100)

    annotationStore.load(
      'test-page',
      makeAnnotationData([
        {
          category_type: 'text_block',
          poly: [10, 10, 200, 10, 200, 40, 10, 40],
          ignore: false,
          order: 0,
          anno_id: 0,
          text: '줌 테스트',
        },
      ]),
    )

    const { container } = render(TextOverlay, {
      props: { pointerEvents: 'auto' },
    })

    // The inner transform div should have the CSS transform
    const transformDiv = container.querySelector('[style*="transform: translate"]')
    expect(transformDiv).toBeTruthy()
    const style = (transformDiv as HTMLElement).style.transform
    expect(style).toContain('translate(50px, 100px)')
    expect(style).toContain('scale(2)')
  })
})
