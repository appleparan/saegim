<script lang="ts">
  import { Button } from '$lib/components/ui/button'
  import type {
    CommercialApiProvider,
    EngineType,
    OcrConfigResponse,
    OcrConfigUpdate,
    OcrConnectionTestResponse,
    SplitPipelineOcrProvider,
  } from '$lib/api/types'

  interface Props {
    config: OcrConfigResponse
    saving?: boolean
    testing?: boolean
    testResult?: OcrConnectionTestResponse | null
    onsave?: (config: OcrConfigUpdate) => void
    ontest?: (config: OcrConfigUpdate) => void
  }

  let {
    config,
    saving = false,
    testing = false,
    testResult = null,
    onsave,
    ontest,
  }: Props = $props()

  // Local form state
  let engineType = $state<EngineType>('pdfminer')
  let enabledEngines = $state<Set<EngineType>>(new Set())

  // Commercial API state
  let caProvider = $state<CommercialApiProvider>('gemini')
  let caApiKey = $state('')
  let caModel = $state('gemini-3-flash-preview')

  // vLLM server state
  let vllmHost = $state('localhost')
  let vllmPort = $state(8000)
  let vllmModel = $state('datalab-to/chandra')

  // Split pipeline state
  let spDoclingModel = $state('ibm-granite/granite-docling-258M')
  let spOcrProvider = $state<SplitPipelineOcrProvider>('gemini')
  let spOcrApiKey = $state('')
  let spOcrHost = $state('localhost')
  let spOcrPort = $state(8000)
  let spOcrModel = $state('gemini-3-flash-preview')

  $effect(() => {
    engineType = config.engine_type
    // Restore enabled engines from config, default to just the primary engine
    const saved = config.enabled_engines ?? []
    enabledEngines = new Set(saved.length > 0 ? saved : [config.engine_type])
    // Ensure primary engine is always enabled
    enabledEngines.add(config.engine_type)

    // Commercial API
    caProvider = config.commercial_api?.provider ?? 'gemini'
    caApiKey = config.commercial_api?.api_key || config.env_gemini_api_key || ''
    caModel = config.commercial_api?.model ?? 'gemini-3-flash-preview'
    // vLLM server
    vllmHost = config.vllm?.host ?? 'localhost'
    vllmPort = config.vllm?.port ?? 8000
    vllmModel = config.vllm?.model ?? 'datalab-to/chandra'
    // Split pipeline
    spDoclingModel =
      config.split_pipeline?.docling_model_name ?? 'ibm-granite/granite-docling-258M'
    spOcrProvider = config.split_pipeline?.ocr_provider ?? 'gemini'
    spOcrApiKey = config.split_pipeline?.ocr_api_key || config.env_gemini_api_key || ''
    spOcrHost = config.split_pipeline?.ocr_host ?? 'localhost'
    spOcrPort = config.split_pipeline?.ocr_port ?? 8000
    spOcrModel = config.split_pipeline?.ocr_model ?? 'gemini-3-flash-preview'
  })

  function isEngineValid(et: EngineType): boolean {
    if (et === 'pdfminer') return true
    if (et === 'commercial_api') {
      return caProvider === 'gemini' && caApiKey.trim().length > 0
    }
    if (et === 'vllm') {
      return vllmHost.trim().length > 0 && vllmPort > 0
    }
    if (et === 'split_pipeline') {
      if (spDoclingModel.trim().length === 0) return false
      if (spOcrProvider === 'gemini') return spOcrApiKey.trim().length > 0
      if (spOcrProvider === 'vllm') return spOcrHost.trim().length > 0 && spOcrPort > 0
      return false
    }
    return false
  }

  let isValid = $derived.by(() => {
    // Primary engine must be valid
    if (!isEngineValid(engineType)) return false
    // All enabled non-pdfminer engines must be valid
    for (const et of enabledEngines) {
      if (et !== 'pdfminer' && !isEngineValid(et)) return false
    }
    return true
  })

  const engineTypes: { value: EngineType; label: string; description: string }[] = [
    { value: 'pdfminer', label: 'pdfminer', description: '기본 텍스트 추출 (Fallback/CI)' },
    {
      value: 'commercial_api',
      label: 'Gemini API',
      description: 'Google Gemini Full-page VLM OCR',
    },
    {
      value: 'vllm',
      label: 'vLLM 서버',
      description: 'vLLM 호환 서버 (OpenAI API)',
    },
    {
      value: 'split_pipeline',
      label: 'Docling + OCR',
      description: 'Docling 레이아웃 + Gemini/vLLM 텍스트 OCR',
    },
  ]

  /** Engines that need a config panel displayed */
  let enginesNeedingConfig = $derived(
    engineTypes.filter((e) => e.value !== 'pdfminer' && enabledEngines.has(e.value)),
  )

  let needsConnectionTest = $derived(engineType !== 'pdfminer')

  function handleSetPrimary(et: EngineType): void {
    engineType = et
    // Primary engine is always enabled
    enabledEngines = new Set([...enabledEngines, et])
  }

  function handleToggleEnabled(et: EngineType): void {
    // Cannot disable the primary engine
    if (et === engineType) return
    const next = new Set(enabledEngines)
    if (next.has(et)) {
      next.delete(et)
    } else {
      next.add(et)
    }
    enabledEngines = next
  }

  function buildConfig(): OcrConfigUpdate {
    const result: OcrConfigUpdate = {
      engine_type: engineType,
      enabled_engines: [...enabledEngines],
      commercial_api: enabledEngines.has('commercial_api')
        ? {
            provider: caProvider,
            api_key: caApiKey.trim(),
            model: caModel.trim(),
          }
        : undefined,
      vllm: enabledEngines.has('vllm')
        ? { host: vllmHost.trim(), port: vllmPort, model: vllmModel.trim() }
        : undefined,
      split_pipeline: enabledEngines.has('split_pipeline')
        ? {
            docling_model_name: spDoclingModel.trim(),
            ocr_provider: spOcrProvider,
            ocr_api_key: spOcrProvider === 'gemini' ? spOcrApiKey.trim() : undefined,
            ocr_host: spOcrProvider === 'vllm' ? spOcrHost.trim() : undefined,
            ocr_port: spOcrProvider === 'vllm' ? spOcrPort : undefined,
            ocr_model: spOcrModel.trim(),
          }
        : undefined,
    }
    return result
  }

  function handleSave() {
    onsave?.(buildConfig())
  }

  function handleTest() {
    ontest?.(buildConfig())
  }
</script>

<div class="space-y-6">
  <!-- Engine Type Selection: primary + enabled toggle -->
  <div>
    <h3 class="text-foreground mb-1 text-sm font-semibold">OCR 엔진 타입</h3>
    <p class="text-muted-foreground mb-3 text-xs">
      기본 엔진을 선택하고, 레이블링에서 사용할 추가 엔진을 활성화하세요.
    </p>
    <div class="grid grid-cols-2 gap-3">
      {#each engineTypes as e (e.value)}
        {@const isPrimary = engineType === e.value}
        {@const isEnabled = enabledEngines.has(e.value)}
        <div
          class="relative rounded-lg border-2 p-3 text-left transition-all
            {isPrimary
            ? 'border-primary bg-primary/10'
            : isEnabled
              ? 'border-emerald-400 bg-emerald-50 dark:border-emerald-600 dark:bg-emerald-950/30'
              : 'border-border bg-card'}"
        >
          <!-- Primary selector (radio) -->
          <button
            type="button"
            class="w-full text-left"
            onclick={() => handleSetPrimary(e.value)}
          >
            <div class="flex items-center gap-2">
              <div
                class="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-2 transition-colors
                  {isPrimary ? 'border-primary bg-primary' : 'border-muted-foreground'}"
              >
                {#if isPrimary}
                  <div class="h-1.5 w-1.5 rounded-full bg-white"></div>
                {/if}
              </div>
              <span class="text-foreground text-sm font-medium">{e.label}</span>
              {#if isPrimary}
                <span
                  class="bg-primary/20 text-primary rounded px-1.5 py-0.5 text-[10px] font-semibold"
                >
                  기본
                </span>
              {/if}
            </div>
            <div class="text-muted-foreground mt-1 pl-6 text-xs">{e.description}</div>
          </button>

          <!-- Enable toggle (checkbox) — only for non-primary engines -->
          {#if !isPrimary && e.value !== 'pdfminer'}
            <button
              type="button"
              class="absolute right-2 top-2 flex items-center gap-1 rounded px-1.5 py-0.5 text-xs transition-colors
                {isEnabled
                ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300'
                : 'text-muted-foreground hover:bg-muted'}"
              onclick={() => handleToggleEnabled(e.value)}
            >
              {#if isEnabled}
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                활성
              {:else}
                추가
              {/if}
            </button>
          {/if}
        </div>
      {/each}
    </div>
  </div>

  <!-- Config panels for each enabled non-pdfminer engine -->
  {#each enginesNeedingConfig as e (e.value)}
    {@const isPrimary = engineType === e.value}
    <div class="space-y-3">
      <div class="flex items-center gap-2">
        <h3 class="text-foreground text-sm font-semibold">{e.label} 설정</h3>
        {#if isPrimary}
          <span class="bg-primary/20 text-primary rounded px-1.5 py-0.5 text-[10px] font-semibold">
            기본
          </span>
        {:else}
          <span class="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
            추가 엔진
          </span>
        {/if}
      </div>

      {#if e.value === 'commercial_api'}
        <div class="bg-muted border-border space-y-3 rounded-lg border p-4">
          <h4 class="text-foreground text-sm font-medium">Google Gemini</h4>
          <div>
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="ca-api-key">
              API Key
            </label>
            <input
              id="ca-api-key"
              type="password"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
                py-2 text-sm focus:ring-1"
              placeholder="Google Gemini API Key"
              bind:value={caApiKey}
            />
          </div>
          <div>
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="ca-model">
              모델
            </label>
            <select
              id="ca-model"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
                py-2 text-sm focus:ring-1"
              bind:value={caModel}
            >
              <option value="gemini-3-flash-preview">gemini-3-flash-preview</option>
              <option value="gemini-3-pro-preview">gemini-3-pro-preview</option>
              <option value="gemini-3.1-pro-preview">gemini-3.1-pro-preview</option>
            </select>
          </div>
        </div>
      {/if}

      {#if e.value === 'vllm'}
        <div class="bg-muted border-border space-y-3 rounded-lg border p-4">
          <h4 class="text-foreground text-sm font-medium">vLLM 서버</h4>
          <div class="grid grid-cols-3 gap-3">
            <div class="col-span-2">
              <label class="text-muted-foreground mb-1 block text-xs font-medium" for="vllm-host">
                호스트
              </label>
              <input
                id="vllm-host"
                type="text"
                class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
                  py-2 text-sm focus:ring-1"
                placeholder="localhost"
                bind:value={vllmHost}
              />
            </div>
            <div>
              <label class="text-muted-foreground mb-1 block text-xs font-medium" for="vllm-port">
                포트
              </label>
              <input
                id="vllm-port"
                type="number"
                class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
                  py-2 text-sm focus:ring-1"
                placeholder="8000"
                min="1"
                max="65535"
                bind:value={vllmPort}
              />
            </div>
          </div>
          <div>
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="vllm-model">
              모델
            </label>
            <input
              id="vllm-model"
              type="text"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
                py-2 text-sm focus:ring-1"
              placeholder="datalab-to/chandra"
              bind:value={vllmModel}
            />
          </div>
        </div>
      {/if}

      {#if e.value === 'split_pipeline'}
        <div class="bg-muted border-border space-y-3 rounded-lg border p-4">
          <h4 class="text-foreground text-sm font-medium">Docling 레이아웃 감지</h4>
          <div>
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="sp-docling-model">
              Docling 모델
            </label>
            <input
              id="sp-docling-model"
              type="text"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
                py-2 text-sm focus:ring-1"
              placeholder="ibm-granite/granite-docling-258M"
              bind:value={spDoclingModel}
            />
          </div>
        </div>

        <div class="bg-muted border-border space-y-3 rounded-lg border p-4">
          <h4 class="text-foreground text-sm font-medium">OCR 프로바이더</h4>
          <div class="mb-3 grid grid-cols-2 gap-3">
            <button
              type="button"
              class="rounded-lg border-2 p-2 text-left transition-all
                {spOcrProvider === 'gemini'
                ? 'border-primary bg-primary/10'
                : 'border-border hover:border-border bg-card'}"
              onclick={() => (spOcrProvider = 'gemini')}
            >
              <div class="text-foreground text-sm font-medium">Google Gemini</div>
            </button>
            <button
              type="button"
              class="rounded-lg border-2 p-2 text-left transition-all
                {spOcrProvider === 'vllm'
                ? 'border-primary bg-primary/10'
                : 'border-border hover:border-border bg-card'}"
              onclick={() => (spOcrProvider = 'vllm')}
            >
              <div class="text-foreground text-sm font-medium">vLLM</div>
            </button>
          </div>

          {#if spOcrProvider === 'gemini'}
            <div>
              <label class="text-muted-foreground mb-1 block text-xs font-medium" for="sp-ocr-api-key">
                API Key
              </label>
              <input
                id="sp-ocr-api-key"
                type="password"
                class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
                  py-2 text-sm focus:ring-1"
                placeholder="Google Gemini API Key"
                bind:value={spOcrApiKey}
              />
            </div>
          {/if}

          {#if spOcrProvider === 'vllm'}
            <div class="grid grid-cols-3 gap-3">
              <div class="col-span-2">
                <label class="text-muted-foreground mb-1 block text-xs font-medium" for="sp-ocr-host">
                  호스트
                </label>
                <input
                  id="sp-ocr-host"
                  type="text"
                  class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
                    py-2 text-sm focus:ring-1"
                  placeholder="localhost"
                  bind:value={spOcrHost}
                />
              </div>
              <div>
                <label class="text-muted-foreground mb-1 block text-xs font-medium" for="sp-ocr-port">
                  포트
                </label>
                <input
                  id="sp-ocr-port"
                  type="number"
                  class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
                    py-2 text-sm focus:ring-1"
                  placeholder="8000"
                  min="1"
                  max="65535"
                  bind:value={spOcrPort}
                />
              </div>
            </div>
          {/if}

          <div>
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="sp-ocr-model">
              모델
            </label>
            <input
              id="sp-ocr-model"
              type="text"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
                py-2 text-sm focus:ring-1"
              placeholder="gemini-3-flash-preview"
              bind:value={spOcrModel}
            />
          </div>
        </div>
      {/if}
    </div>
  {/each}

  <!-- Connection Test Result -->
  {#if testResult}
    <div
      class="rounded-lg border p-3 text-sm
        {testResult.success
        ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300'
        : 'bg-destructive/10 dark:bg-destructive/20 border-destructive/30 text-destructive'}"
    >
      {testResult.message}
    </div>
  {/if}

  <!-- Action Buttons -->
  <div class="flex items-center justify-end gap-2">
    {#if needsConnectionTest}
      <Button variant="outline" disabled={!isValid || testing} onclick={handleTest}>
        {testing ? '테스트 중...' : '연결 테스트'}
      </Button>
    {/if}
    <Button variant="default" disabled={!isValid || saving} onclick={handleSave}>
      {saving ? '저장 중...' : '설정 저장'}
    </Button>
  </div>
</div>
