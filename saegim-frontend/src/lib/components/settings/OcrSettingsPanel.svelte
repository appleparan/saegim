<script lang="ts">
  import { Button } from '$lib/components/ui/button'
  import EngineCard from './EngineCard.svelte'
  import EngineAddDialog from './EngineAddDialog.svelte'
  import type {
    EngineInstanceCreate,
    OcrConfigResponse,
    OcrConnectionTestResponse,
  } from '$lib/api/types'

  interface Props {
    config: OcrConfigResponse
    connectionStatuses?: Record<string, OcrConnectionTestResponse | null>
    testingEngines?: Set<string>
    onadd?: (data: EngineInstanceCreate) => void
    onupdate?: (engineId: string, data: { name?: string; config?: Record<string, unknown> }) => void
    ondelete?: (engineId: string) => void
    onsetdefault?: (engineId: string) => void
    ontest?: (engineId: string) => void
  }

  let {
    config,
    connectionStatuses = {},
    testingEngines = new Set(),
    onadd,
    onupdate,
    ondelete,
    onsetdefault,
    ontest,
  }: Props = $props()

  let showAddDialog = $state(false)

  let engineEntries = $derived(Object.entries(config.engines))
  let hasEngines = $derived(engineEntries.length > 0)
</script>

<div class="space-y-4">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h3 class="text-foreground text-sm font-semibold">OCR 엔진 관리</h3>
      <p class="text-muted-foreground text-xs">
        엔진 인스턴스를 등록하고 관리하세요. ★ 표시된 엔진이 전체 페이지 OCR에 사용됩니다.
      </p>
    </div>
    <Button variant="outline" size="sm" onclick={() => (showAddDialog = true)}>
      <svg class="mr-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
      </svg>
      엔진 추가
    </Button>
  </div>

  <!-- Engine Cards -->
  {#if hasEngines}
    <div class="space-y-3">
      {#each engineEntries as [engineId, engine] (engineId)}
        <EngineCard
          {engineId}
          {engine}
          isDefault={config.default_engine_id === engineId}
          connectionStatus={connectionStatuses[engineId] ?? null}
          isTesting={testingEngines.has(engineId)}
          onsetdefault={() => onsetdefault?.(engineId)}
          onupdate={(data) => onupdate?.(engineId, data)}
          ondelete={() => ondelete?.(engineId)}
          ontest={() => ontest?.(engineId)}
        />
      {/each}
    </div>
  {:else}
    <div class="border-border rounded-lg border border-dashed p-8 text-center">
      <p class="text-muted-foreground text-sm">등록된 엔진이 없습니다.</p>
      <p class="text-muted-foreground mt-1 text-xs">
        "엔진 추가" 버튼을 눌러 OCR 엔진을 등록하세요.
      </p>
    </div>
  {/if}

  <!-- pdfminer fallback note -->
  <div class="border-border bg-muted/50 rounded-lg border p-3">
    <div class="flex items-center gap-2">
      <svg class="text-muted-foreground h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <div>
        <span class="text-foreground text-xs font-medium">pdfminer</span>
        <span class="text-muted-foreground text-xs">
          — 항상 사용 가능한 기본 폴백 엔진입니다. 기본 엔진이 설정되지 않으면 pdfminer가 사용됩니다.
        </span>
      </div>
    </div>
  </div>
</div>

<!-- Add Engine Dialog -->
<EngineAddDialog
  bind:open={showAddDialog}
  envGeminiApiKey={config.env_gemini_api_key ?? ''}
  onadd={onadd}
/>
