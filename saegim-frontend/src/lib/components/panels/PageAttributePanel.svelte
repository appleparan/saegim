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
  import { Switch } from '$lib/components/ui/switch'
  import { Label } from '$lib/components/ui/label'

  let attr = $derived(annotationStore.pageAttribute)
</script>

{#if attr}
  <div class="space-y-4 p-3">
    <h3 class="text-foreground text-sm font-semibold">페이지 속성</h3>

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

    <div class="border-border space-y-3 border-t pt-3">
      <h4 class="text-muted-foreground text-xs font-medium uppercase">특수 속성</h4>
      <div class="flex items-center gap-2">
        <Switch
          checked={attr.watermark ?? false}
          onCheckedChange={() =>
            annotationStore.updatePageAttribute({
              watermark: !(attr?.watermark ?? false),
            })}
        />
        <Label class="text-sm">워터마크</Label>
      </div>
      <div class="flex items-center gap-2">
        <Switch
          checked={attr.fuzzy_scan ?? false}
          onCheckedChange={() =>
            annotationStore.updatePageAttribute({
              fuzzy_scan: !(attr?.fuzzy_scan ?? false),
            })}
        />
        <Label class="text-sm">흐린 스캔</Label>
      </div>
      <div class="flex items-center gap-2">
        <Switch
          checked={attr.colorful_background ?? false}
          onCheckedChange={() =>
            annotationStore.updatePageAttribute({
              colorful_background: !(attr?.colorful_background ?? false),
            })}
        />
        <Label class="text-sm">컬러 배경</Label>
      </div>
    </div>
  </div>
{:else}
  <div class="p-3 text-center">
    <p class="text-muted-foreground py-8 text-sm">페이지 데이터를 불러오는 중...</p>
  </div>
{/if}
