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
  import Select from '$lib/components/common/Select.svelte'
  import { Switch } from '$lib/components/ui/switch'
  import { Label } from '$lib/components/ui/label'

  let attr = $derived(annotationStore.pageAttribute)
</script>

{#if attr}
  <div class="space-y-4 p-3">
    <h3 class="text-foreground text-sm font-semibold">Page Attributes</h3>

    <Select
      label="Data Source"
      value={attr.data_source ?? ''}
      options={DATA_SOURCES}
      labels={DATA_SOURCE_LABELS}
      onchange={(v) => annotationStore.updatePageAttribute({ data_source: v })}
    />

    <Select
      label="Language"
      value={attr.language ?? ''}
      options={PAGE_LANGUAGES}
      labels={PAGE_LANGUAGE_LABELS}
      onchange={(v) => annotationStore.updatePageAttribute({ language: v })}
    />

    <Select
      label="Layout"
      value={attr.layout ?? ''}
      options={PAGE_LAYOUTS}
      labels={PAGE_LAYOUT_LABELS}
      onchange={(v) => annotationStore.updatePageAttribute({ layout: v })}
    />

    <div class="border-border space-y-3 border-t pt-3">
      <h4 class="text-muted-foreground text-xs font-medium uppercase">Special Attributes</h4>
      <div class="flex items-center gap-2">
        <Switch
          checked={attr.watermark ?? false}
          onCheckedChange={() =>
            annotationStore.updatePageAttribute({
              watermark: !(attr?.watermark ?? false),
            })}
        />
        <Label class="text-sm">Watermark</Label>
      </div>
      <div class="flex items-center gap-2">
        <Switch
          checked={attr.fuzzy_scan ?? false}
          onCheckedChange={() =>
            annotationStore.updatePageAttribute({
              fuzzy_scan: !(attr?.fuzzy_scan ?? false),
            })}
        />
        <Label class="text-sm">Blurry Scan</Label>
      </div>
      <div class="flex items-center gap-2">
        <Switch
          checked={attr.colorful_background ?? false}
          onCheckedChange={() =>
            annotationStore.updatePageAttribute({
              colorful_background: !(attr?.colorful_background ?? false),
            })}
        />
        <Label class="text-sm">Color Background</Label>
      </div>
    </div>
  </div>
{:else}
  <div class="p-3 text-center">
    <p class="text-muted-foreground py-8 text-sm">Loading page data...</p>
  </div>
{/if}
