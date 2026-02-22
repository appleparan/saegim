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
  let engineType = $state<EngineType>('pymupdf')

  // Commercial API state
  let caProvider = $state<CommercialApiProvider>('gemini')
  let caApiKey = $state('')
  let caModel = $state('gemini-3-flash-preview')

  // Integrated server state
  let isHost = $state('localhost')
  let isPort = $state(8000)
  let isModel = $state('datalab-to/chandra')

  // Split pipeline state
  let spLayoutUrl = $state('http://localhost:18811')
  let spOcrProvider = $state<SplitPipelineOcrProvider>('gemini')
  let spOcrApiKey = $state('')
  let spOcrHost = $state('localhost')
  let spOcrPort = $state(8000)
  let spOcrModel = $state('gemini-3-flash-preview')

  $effect(() => {
    engineType = config.engine_type
    // Commercial API
    caProvider = config.commercial_api?.provider ?? 'gemini'
    caApiKey = config.commercial_api?.api_key ?? ''
    caModel = config.commercial_api?.model ?? 'gemini-3-flash-preview'
    // Integrated server
    isHost = config.integrated_server?.host ?? 'localhost'
    isPort = config.integrated_server?.port ?? 8000
    isModel = config.integrated_server?.model ?? 'datalab-to/chandra'
    // Split pipeline
    spLayoutUrl = config.split_pipeline?.layout_server_url ?? 'http://localhost:18811'
    spOcrProvider = config.split_pipeline?.ocr_provider ?? 'gemini'
    spOcrApiKey = config.split_pipeline?.ocr_api_key ?? ''
    spOcrHost = config.split_pipeline?.ocr_host ?? 'localhost'
    spOcrPort = config.split_pipeline?.ocr_port ?? 8000
    spOcrModel = config.split_pipeline?.ocr_model ?? 'gemini-3-flash-preview'
  })

  let isValid = $derived.by(() => {
    if (engineType === 'pymupdf') return true
    if (engineType === 'commercial_api') {
      if (caProvider === 'gemini') return caApiKey.trim().length > 0
      return false
    }
    if (engineType === 'integrated_server') {
      return isHost.trim().length > 0 && isPort > 0
    }
    if (engineType === 'split_pipeline') {
      if (spLayoutUrl.trim().length === 0) return false
      if (spOcrProvider === 'gemini') return spOcrApiKey.trim().length > 0
      if (spOcrProvider === 'vllm') return spOcrHost.trim().length > 0 && spOcrPort > 0
      return false
    }
    return false
  })

  const engineTypes: { value: EngineType; label: string; description: string }[] = [
    { value: 'pymupdf', label: 'PyMuPDF', description: '기본 텍스트 추출 (Fallback/CI)' },
    {
      value: 'commercial_api',
      label: '상업용 VLM API',
      description: 'Gemini 등 Full-page OCR',
    },
    {
      value: 'integrated_server',
      label: '통합 파이프라인 서버',
      description: 'PP-StructureV3 + PP-OCR',
    },
    {
      value: 'split_pipeline',
      label: '분리 파이프라인',
      description: '레이아웃 서버 + 별도 OCR',
    },
  ]

  let needsConnectionTest = $derived(engineType !== 'pymupdf')

  function buildConfig(): OcrConfigUpdate {
    if (engineType === 'pymupdf') {
      return { engine_type: 'pymupdf' }
    }
    if (engineType === 'commercial_api') {
      return {
        engine_type: 'commercial_api',
        commercial_api: {
          provider: caProvider,
          api_key: caApiKey.trim(),
          model: caModel.trim(),
        },
      }
    }
    if (engineType === 'integrated_server') {
      return {
        engine_type: 'integrated_server',
        integrated_server: { host: isHost.trim(), port: isPort, model: isModel.trim() },
      }
    }
    // split_pipeline
    return {
      engine_type: 'split_pipeline',
      split_pipeline: {
        layout_server_url: spLayoutUrl.trim(),
        ocr_provider: spOcrProvider,
        ocr_api_key: spOcrProvider === 'gemini' ? spOcrApiKey.trim() : undefined,
        ocr_host: spOcrProvider === 'vllm' ? spOcrHost.trim() : undefined,
        ocr_port: spOcrProvider === 'vllm' ? spOcrPort : undefined,
        ocr_model: spOcrModel.trim(),
      },
    }
  }

  function handleSave() {
    onsave?.(buildConfig())
  }

  function handleTest() {
    ontest?.(buildConfig())
  }
</script>

<div class="space-y-6">
  <!-- Engine Type Selection -->
  <div>
    <h3 class="text-foreground mb-3 text-sm font-semibold">OCR 엔진 타입</h3>
    <div class="grid grid-cols-2 gap-3">
      {#each engineTypes as e}
        <button
          type="button"
          class="rounded-lg border-2 p-3 text-left transition-all
            {engineType === e.value
            ? 'border-primary bg-primary/10'
            : 'border-border hover:border-border bg-card'}"
          onclick={() => (engineType = e.value)}
        >
          <div class="text-foreground text-sm font-medium">{e.label}</div>
          <div class="text-muted-foreground mt-0.5 text-xs">{e.description}</div>
        </button>
      {/each}
    </div>
  </div>

  <!-- Commercial API Config -->
  {#if engineType === 'commercial_api'}
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
        <label class="text-muted-foreground mb-1 block text-xs font-medium" for="ca-model"
          >모델</label
        >
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

  <!-- Integrated Server Config -->
  {#if engineType === 'integrated_server'}
    <div class="bg-muted border-border space-y-3 rounded-lg border p-4">
      <h4 class="text-foreground text-sm font-medium">통합 파이프라인 서버</h4>
      <div class="grid grid-cols-3 gap-3">
        <div class="col-span-2">
          <label class="text-muted-foreground mb-1 block text-xs font-medium" for="is-host"
            >호스트</label
          >
          <input
            id="is-host"
            type="text"
            class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
              py-2 text-sm focus:ring-1"
            placeholder="localhost"
            bind:value={isHost}
          />
        </div>
        <div>
          <label class="text-muted-foreground mb-1 block text-xs font-medium" for="is-port"
            >포트</label
          >
          <input
            id="is-port"
            type="number"
            class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
              py-2 text-sm focus:ring-1"
            placeholder="8000"
            min="1"
            max="65535"
            bind:value={isPort}
          />
        </div>
      </div>
      <div>
        <label class="text-muted-foreground mb-1 block text-xs font-medium" for="is-model"
          >모델</label
        >
        <input
          id="is-model"
          type="text"
          class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
            py-2 text-sm focus:ring-1"
          placeholder="datalab-to/chandra"
          bind:value={isModel}
        />
      </div>
    </div>
  {/if}

  <!-- Split Pipeline Config -->
  {#if engineType === 'split_pipeline'}
    <div class="bg-muted border-border space-y-3 rounded-lg border p-4">
      <h4 class="text-foreground text-sm font-medium">레이아웃 서버</h4>
      <div>
        <label class="text-muted-foreground mb-1 block text-xs font-medium" for="sp-layout-url">
          레이아웃 서버 URL
        </label>
        <input
          id="sp-layout-url"
          type="text"
          class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3
            py-2 text-sm focus:ring-1"
          placeholder="http://localhost:18811"
          bind:value={spLayoutUrl}
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
