<script lang="ts">
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { isTextBlock } from '$lib/types/element-groups'
  import { polyToRect } from '$lib/utils/bbox'
  import { estimateFontSize } from '$lib/utils/text-layout'

  interface Props {
    /** Controls whether the text overlay accepts pointer events. */
    pointerEvents: 'auto' | 'none'
  }

  let { pointerEvents }: Props = $props()

  let textElements = $derived(annotationStore.elements.filter(isTextBlock))
</script>

<div
  class="absolute inset-0 overflow-hidden"
  style="z-index: 20; pointer-events: {pointerEvents};"
>
  <div
    style="
      transform-origin: 0 0;
      transform: translate({canvasStore.offsetX}px, {canvasStore.offsetY}px) scale({canvasStore.scale});
      position: absolute;
      width: {canvasStore.imageWidth}px;
      height: {canvasStore.imageHeight}px;
    "
  >
    {#each textElements as el (el.anno_id)}
      {@const rect = polyToRect(el.poly)}
      {@const fontSize = estimateFontSize(el.poly)}
      <div
        role="textbox"
        tabindex="-1"
        style="
          position: absolute;
          left: {rect.x}px;
          top: {rect.y}px;
          width: {rect.width}px;
          height: {rect.height}px;
          font-size: {fontSize}px;
          line-height: 1.2;
          color: transparent;
          user-select: text;
          cursor: text;
          overflow: hidden;
          border: 1px solid transparent;
          transition: border-color 0.15s, background-color 0.15s;
        "
        class="hover:border-blue-400/50 hover:bg-blue-50/10"
        onclick={() => annotationStore.selectElement(el.anno_id)}
        onkeydown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            annotationStore.selectElement(el.anno_id)
          }
        }}
      >
        {el.text ?? ''}
      </div>
    {/each}
  </div>
</div>
