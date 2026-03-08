<script lang="ts">
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { polyToRect } from '$lib/utils/bbox'
  import { getCategoryColor } from '$lib/utils/color'
</script>

{#if canvasStore.showReadingOrder || canvasStore.showElementIndex}
  <div
    class="absolute inset-0 overflow-hidden"
    style="z-index: 25; pointer-events: none;"
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
      {#each annotationStore.elements as el (el.anno_id)}
        {@const rect = polyToRect(el.poly)}
        {@const color = getCategoryColor(el.category_type)}

        <!-- Bbox outline (element index mode) -->
        {#if canvasStore.showElementIndex}
          <div
            style="
              position: absolute;
              left: {rect.x}px;
              top: {rect.y}px;
              width: {rect.width}px;
              height: {rect.height}px;
              border: 2px solid {color};
              background-color: {color}10;
              pointer-events: none;
            "
          ></div>
        {/if}

        <!-- Number badge -->
        <div
          style="
            position: absolute;
            left: {rect.x - 4}px;
            top: {rect.y - 4}px;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background-color: {color};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 700;
            color: white;
            line-height: 1;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            pointer-events: none;
            user-select: none;
          "
        >
          {canvasStore.showReadingOrder ? el.order : el.anno_id}
        </div>
      {/each}
    </div>
  </div>
{/if}
