<script lang="ts">
  import { Button } from '$lib/components/ui/button'
  import type {
    EngineInstance,
    OcrConnectionTestResponse,
    RegisterableEngineType,
  } from '$lib/api/types'

  interface Props {
    engineId: string
    engine: EngineInstance
    isDefault: boolean
    connectionStatus?: OcrConnectionTestResponse | null
    isTesting?: boolean
    onsetdefault?: () => void
    onupdate?: (data: { name?: string; config?: Record<string, unknown> }) => void
    ondelete?: () => void
    ontest?: () => void
  }

  let {
    engineId,
    engine,
    isDefault,
    connectionStatus = null,
    isTesting = false,
    onsetdefault,
    onupdate,
    ondelete,
    ontest,
  }: Props = $props()

  let isExpanded = $state(false)
  let editName = $state('')
  let editConfig = $state<Record<string, string | number>>({})

  const ENGINE_LABELS: Record<RegisterableEngineType, string> = {
    commercial_api: 'Gemini API',
    vllm: 'vLLM',
    split_pipeline: 'Docling + OCR',
  }

  function initEdit() {
    editName = engine.name
    editConfig = { ...(engine.config as Record<string, string | number>) }
  }

  function toggleExpand() {
    if (!isExpanded) initEdit()
    isExpanded = !isExpanded
  }

  function handleSave() {
    onupdate?.({ name: editName, config: editConfig })
    isExpanded = false
  }

  function getSubtitle(): string {
    const type = ENGINE_LABELS[engine.engine_type] || engine.engine_type
    const cfg = engine.config as Record<string, unknown>
    if (engine.engine_type === 'vllm') {
      return `${type} \u00b7 ${cfg.host ?? 'localhost'}:${cfg.port ?? 8000}`
    }
    if (engine.engine_type === 'commercial_api') {
      return `${type} \u00b7 ${cfg.model ?? ''}`
    }
    if (engine.engine_type === 'split_pipeline') {
      return `${type} \u00b7 ${cfg.ocr_provider ?? ''}`
    }
    return type
  }
</script>

<div
  class="border-border rounded-lg border transition-all
    {isDefault ? 'ring-primary/30 ring-2' : ''}"
>
  <!-- Card Header -->
  <div class="flex items-center gap-3 p-4">
    <!-- Default star -->
    <button
      type="button"
      class="shrink-0 transition-colors
        {isDefault
        ? 'text-amber-500'
        : 'text-muted-foreground/30 hover:text-amber-400'}"
      title={isDefault ? '기본 엔진' : '기본 엔진으로 설정'}
      onclick={() => !isDefault && onsetdefault?.()}
    >
      <svg class="h-5 w-5" fill={isDefault ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
      </svg>
    </button>

    <!-- Name & subtitle -->
    <button type="button" class="min-w-0 flex-1 text-left" onclick={toggleExpand}>
      <div class="text-foreground text-sm font-medium">{engine.name}</div>
      <div class="text-muted-foreground truncate text-xs">{getSubtitle()}</div>
    </button>

    <!-- Connection status icon -->
    <div class="shrink-0">
      {#if isTesting}
        <div class="text-muted-foreground animate-spin">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </div>
      {:else if connectionStatus?.success === true}
        <div class="text-emerald-500" title="연결됨">
          <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <circle cx="10" cy="10" r="5" />
          </svg>
        </div>
      {:else if connectionStatus?.success === false}
        <div class="text-destructive" title={connectionStatus.message}>
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
      {:else}
        <div class="text-muted-foreground/40" title="미테스트">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      {/if}
    </div>

    <!-- Delete button -->
    <button
      type="button"
      class="text-muted-foreground hover:text-destructive shrink-0 transition-colors"
      title="삭제"
      onclick={() => ondelete?.()}
    >
      <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
      </svg>
    </button>
  </div>

  <!-- Expanded edit form -->
  {#if isExpanded}
    <div class="border-border space-y-3 border-t p-4">
      <div>
        <label class="text-muted-foreground mb-1 block text-xs font-medium" for="edit-name-{engineId}">이름</label>
        <input
          id="edit-name-{engineId}"
          type="text"
          class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
          bind:value={editName}
        />
      </div>

      {#if engine.engine_type === 'commercial_api'}
        <div>
          <label class="text-muted-foreground mb-1 block text-xs font-medium" for="edit-apikey-{engineId}">API Key</label>
          <input
            id="edit-apikey-{engineId}"
            type="password"
            class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
            value={String(editConfig.api_key ?? '')}
            oninput={(e) => (editConfig = { ...editConfig, api_key: (e.target as HTMLInputElement).value })}
          />
        </div>
        <div>
          <label class="text-muted-foreground mb-1 block text-xs font-medium" for="edit-model-{engineId}">모델</label>
          <select
            id="edit-model-{engineId}"
            class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
            value={String(editConfig.model ?? 'gemini-3-flash-preview')}
            onchange={(e) => (editConfig = { ...editConfig, model: (e.target as HTMLSelectElement).value })}
          >
            <option value="gemini-3-flash-preview">gemini-3-flash-preview (Flash)</option>
            <option value="gemini-3.1-pro-preview">gemini-3.1-pro-preview (Pro)</option>
          </select>
        </div>
        <div>
          <label class="text-muted-foreground mb-1 block text-xs font-medium" for="edit-prompt-{engineId}">OCR 프롬프트 (선택)</label>
          <textarea
            id="edit-prompt-{engineId}"
            class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
            rows="4"
            placeholder="비워두면 기본 레이아웃 분석 프롬프트를 사용합니다."
            value={String(editConfig.prompt ?? '')}
            oninput={(e) => (editConfig = { ...editConfig, prompt: (e.target as HTMLTextAreaElement).value })}
          ></textarea>
        </div>
      {/if}

      {#if engine.engine_type === 'vllm'}
        <div class="grid grid-cols-3 gap-3">
          <div class="col-span-2">
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="edit-host-{engineId}">호스트</label>
            <input
              id="edit-host-{engineId}"
              type="text"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
              value={String(editConfig.host ?? 'localhost')}
              oninput={(e) => (editConfig = { ...editConfig, host: (e.target as HTMLInputElement).value })}
            />
          </div>
          <div>
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="edit-port-{engineId}">포트</label>
            <input
              id="edit-port-{engineId}"
              type="number"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
              value={editConfig.port ?? 8000}
              oninput={(e) => (editConfig = { ...editConfig, port: Number((e.target as HTMLInputElement).value) })}
            />
          </div>
        </div>
        <div>
          <label class="text-muted-foreground mb-1 block text-xs font-medium" for="edit-vllm-model-{engineId}">모델</label>
          <input
            id="edit-vllm-model-{engineId}"
            type="text"
            class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
            value={String(editConfig.model ?? '')}
            oninput={(e) => (editConfig = { ...editConfig, model: (e.target as HTMLInputElement).value })}
          />
        </div>
      {/if}

      {#if engine.engine_type === 'split_pipeline'}
        <div>
          <label class="text-muted-foreground mb-1 block text-xs font-medium" for="edit-docling-{engineId}">Docling 모델</label>
          <input
            id="edit-docling-{engineId}"
            type="text"
            class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
            value={String(editConfig.docling_model_name ?? '')}
            oninput={(e) => (editConfig = { ...editConfig, docling_model_name: (e.target as HTMLInputElement).value })}
          />
        </div>
        <div>
          <label class="text-muted-foreground mb-1 block text-xs font-medium" for="edit-sp-provider-{engineId}">OCR Provider</label>
          <select
            id="edit-sp-provider-{engineId}"
            class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
            value={String(editConfig.ocr_provider ?? 'gemini')}
            onchange={(e) => (editConfig = { ...editConfig, ocr_provider: (e.target as HTMLSelectElement).value })}
          >
            <option value="gemini">Gemini</option>
            <option value="vllm">vLLM</option>
          </select>
        </div>
      {/if}

      <!-- Connection test result (inline) -->
      {#if connectionStatus}
        <div
          class="rounded-md p-2 text-xs
            {connectionStatus.success
            ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300'
            : 'bg-destructive/10 text-destructive dark:bg-destructive/20'}"
        >
          {connectionStatus.message}
        </div>
      {/if}

      <div class="flex items-center justify-end gap-2 pt-1">
        <Button variant="outline" size="sm" disabled={isTesting} onclick={() => ontest?.()}>
          {isTesting ? '테스트 중...' : '연결 테스트'}
        </Button>
        <Button variant="default" size="sm" onclick={handleSave}>저장</Button>
      </div>
    </div>
  {/if}
</div>
