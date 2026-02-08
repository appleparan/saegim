<script lang="ts">
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import {
    DATA_SOURCES,
    DATA_SOURCE_LABELS,
    PAGE_LANGUAGES,
    PAGE_LANGUAGE_LABELS,
    PAGE_LAYOUTS,
    PAGE_LAYOUT_LABELS,
  } from '$lib/types/categories'
  import type { DataSource, PageLanguage, PageLayout } from '$lib/types/categories'
  import Select from '$lib/components/common/Select.svelte'
  import Toggle from '$lib/components/common/Toggle.svelte'

  let attr = $derived(annotationStore.pageAttribute)
</script>

{#if attr}
  <div class="p-3 space-y-4">
    <h3 class="text-sm font-semibold text-gray-700">페이지 속성</h3>

    <Select
      label="데이터 출처"
      value={attr.data_source ?? ''}
      options={DATA_SOURCES}
      labels={DATA_SOURCE_LABELS}
      onchange={(v) => annotationStore.updatePageAttribute({ data_source: v })}
    />

    <Select
      label="언어"
      value={attr.language ?? ''}
      options={PAGE_LANGUAGES}
      labels={PAGE_LANGUAGE_LABELS}
      onchange={(v) => annotationStore.updatePageAttribute({ language: v })}
    />

    <Select
      label="레이아웃"
      value={attr.layout ?? ''}
      options={PAGE_LAYOUTS}
      labels={PAGE_LAYOUT_LABELS}
      onchange={(v) => annotationStore.updatePageAttribute({ layout: v })}
    />

    <div class="border-t border-gray-100 pt-3 space-y-3">
      <h4 class="text-xs font-medium text-gray-500 uppercase">특수 속성</h4>
      <Toggle
        label="워터마크"
        checked={attr.watermark ?? false}
        onchange={() =>
          annotationStore.updatePageAttribute({
            watermark: !(attr?.watermark ?? false),
          })}
      />
      <Toggle
        label="흐린 스캔"
        checked={attr.fuzzy_scan ?? false}
        onchange={() =>
          annotationStore.updatePageAttribute({
            fuzzy_scan: !(attr?.fuzzy_scan ?? false),
          })}
      />
      <Toggle
        label="컬러 배경"
        checked={attr.colorful_background ?? false}
        onchange={() =>
          annotationStore.updatePageAttribute({
            colorful_background: !(attr?.colorful_background ?? false),
          })}
      />
    </div>
  </div>
{:else}
  <div class="p-3 text-center">
    <p class="text-sm text-gray-400 py-8">페이지 데이터를 불러오는 중...</p>
  </div>
{/if}
