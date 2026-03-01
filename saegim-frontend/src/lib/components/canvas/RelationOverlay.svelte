<script lang="ts">
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { polyToRect } from '$lib/utils/bbox'
  import type { Relation } from '$lib/types/omnidocbench'

  interface Props {
    visible?: boolean
  }

  let { visible = true }: Props = $props()

  /** Color mapping for relation types */
  const RELATION_COLORS: Record<string, string> = {
    parent_son: '#6366f1',
    figure_caption: '#22c55e',
    table_caption: '#f59e0b',
    table_footnote: '#ef4444',
    equation_caption: '#a855f7',
    code_caption: '#06b6d4',
  }

  function getRelationColor(type: string): string {
    return RELATION_COLORS[type] ?? '#94a3b8'
  }

  /** Get center point of an element in screen coordinates */
  function getElementCenter(annoId: number): { x: number; y: number } | null {
    const el = annotationStore.elements.find((e) => e.anno_id === annoId)
    if (!el) return null
    const rect = polyToRect(el.poly)
    return {
      x: (rect.x + rect.width / 2) * canvasStore.scale + canvasStore.offsetX,
      y: (rect.y + rect.height / 2) * canvasStore.scale + canvasStore.offsetY,
    }
  }

  /** Compute line endpoints for each relation */
  let relationLines = $derived.by(() => {
    if (!visible) return []

    return annotationStore.relations
      .map((relation: Relation) => {
        const source = getElementCenter(relation.source_anno_id)
        const target = getElementCenter(relation.target_anno_id)
        if (!source || !target) return null
        return {
          relation,
          x1: source.x,
          y1: source.y,
          x2: target.x,
          y2: target.y,
          color: getRelationColor(relation.relation_type),
        }
      })
      .filter((line): line is NonNullable<typeof line> => line !== null)
  })
</script>

{#if visible && relationLines.length > 0}
  <svg
    class="pointer-events-none absolute inset-0 z-30"
    style="width: 100%; height: 100%;"
  >
    <defs>
      {#each relationLines as line, i}
        <marker
          id="arrow-{i}"
          markerWidth="8"
          markerHeight="6"
          refX="8"
          refY="3"
          orient="auto"
        >
          <polygon
            points="0 0, 8 3, 0 6"
            fill={line.color}
            opacity="0.8"
          />
        </marker>
      {/each}
    </defs>
    {#each relationLines as line, i}
      <line
        x1={line.x1}
        y1={line.y1}
        x2={line.x2}
        y2={line.y2}
        stroke={line.color}
        stroke-width="2"
        stroke-dasharray="6 3"
        opacity="0.7"
        marker-end="url(#arrow-{i})"
      />
    {/each}
  </svg>
{/if}
