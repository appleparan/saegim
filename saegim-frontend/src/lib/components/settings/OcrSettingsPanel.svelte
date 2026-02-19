<script lang="ts">
  import Button from '$lib/components/common/Button.svelte'
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
  let caHost = $state('localhost')
  let caPort = $state(8000)
  let caModel = $state('gemini-2.0-flash')

  // Integrated server state
  let isUrl = $state('http://localhost:18811')

  // Split pipeline state
  let spLayoutUrl = $state('http://localhost:18811')
  let spOcrProvider = $state<SplitPipelineOcrProvider>('gemini')
  let spOcrApiKey = $state('')
  let spOcrHost = $state('localhost')
  let spOcrPort = $state(8000)
  let spOcrModel = $state('gemini-2.0-flash')

  $effect(() => {
    engineType = config.engine_type
    // Commercial API
    caProvider = config.commercial_api?.provider ?? 'gemini'
    caApiKey = config.commercial_api?.api_key ?? ''
    caHost = config.commercial_api?.host ?? 'localhost'
    caPort = config.commercial_api?.port ?? 8000
    caModel = config.commercial_api?.model ?? 'gemini-2.0-flash'
    // Integrated server
    isUrl = config.integrated_server?.url ?? 'http://localhost:18811'
    // Split pipeline
    spLayoutUrl = config.split_pipeline?.layout_server_url ?? 'http://localhost:18811'
    spOcrProvider = config.split_pipeline?.ocr_provider ?? 'gemini'
    spOcrApiKey = config.split_pipeline?.ocr_api_key ?? ''
    spOcrHost = config.split_pipeline?.ocr_host ?? 'localhost'
    spOcrPort = config.split_pipeline?.ocr_port ?? 8000
    spOcrModel = config.split_pipeline?.ocr_model ?? 'gemini-2.0-flash'
  })

  let isValid = $derived.by(() => {
    if (engineType === 'pymupdf') return true
    if (engineType === 'commercial_api') {
      if (caProvider === 'gemini') return caApiKey.trim().length > 0
      if (caProvider === 'vllm') return caHost.trim().length > 0 && caPort > 0
      return false
    }
    if (engineType === 'integrated_server') {
      return isUrl.trim().length > 0
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
      description: 'Gemini, vLLM 등 Full-page OCR',
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
          api_key: caProvider === 'gemini' ? caApiKey.trim() : undefined,
          host: caProvider === 'vllm' ? caHost.trim() : undefined,
          port: caProvider === 'vllm' ? caPort : undefined,
          model: caModel.trim(),
        },
      }
    }
    if (engineType === 'integrated_server') {
      return {
        engine_type: 'integrated_server',
        integrated_server: { url: isUrl.trim() },
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
    <h3 class="text-sm font-semibold text-gray-700 mb-3">OCR 엔진 타입</h3>
    <div class="grid grid-cols-2 gap-3">
      {#each engineTypes as e}
        <button
          type="button"
          class="text-left p-3 rounded-lg border-2 transition-all
            {engineType === e.value
            ? 'border-primary-500 bg-primary-50/50'
            : 'border-gray-200 hover:border-gray-300 bg-white'}"
          onclick={() => (engineType = e.value)}
        >
          <div class="font-medium text-sm text-gray-900">{e.label}</div>
          <div class="text-xs text-gray-500 mt-0.5">{e.description}</div>
        </button>
      {/each}
    </div>
  </div>

  <!-- Commercial API Config -->
  {#if engineType === 'commercial_api'}
    <div class="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <h4 class="text-sm font-medium text-gray-700">VLM 프로바이더</h4>
      <div class="grid grid-cols-2 gap-3 mb-3">
        <button
          type="button"
          class="text-left p-2 rounded-lg border-2 transition-all
            {caProvider === 'gemini'
            ? 'border-primary-500 bg-primary-50/50'
            : 'border-gray-200 hover:border-gray-300 bg-white'}"
          onclick={() => (caProvider = 'gemini')}
        >
          <div class="font-medium text-sm text-gray-900">Google Gemini</div>
        </button>
        <button
          type="button"
          class="text-left p-2 rounded-lg border-2 transition-all
            {caProvider === 'vllm'
            ? 'border-primary-500 bg-primary-50/50'
            : 'border-gray-200 hover:border-gray-300 bg-white'}"
          onclick={() => (caProvider = 'vllm')}
        >
          <div class="font-medium text-sm text-gray-900">vLLM</div>
        </button>
      </div>

      {#if caProvider === 'gemini'}
        <div>
          <label class="block text-xs font-medium text-gray-600 mb-1" for="ca-api-key">
            API Key
          </label>
          <input
            id="ca-api-key"
            type="password"
            class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
              focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
            placeholder="Google Gemini API Key"
            bind:value={caApiKey}
          />
        </div>
      {/if}

      {#if caProvider === 'vllm'}
        <div class="grid grid-cols-3 gap-3">
          <div class="col-span-2">
            <label class="block text-xs font-medium text-gray-600 mb-1" for="ca-host">
              호스트
            </label>
            <input
              id="ca-host"
              type="text"
              class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
                focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
              placeholder="localhost"
              bind:value={caHost}
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1" for="ca-port">
              포트
            </label>
            <input
              id="ca-port"
              type="number"
              class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
                focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
              placeholder="8000"
              min="1"
              max="65535"
              bind:value={caPort}
            />
          </div>
        </div>
      {/if}

      <div>
        <label class="block text-xs font-medium text-gray-600 mb-1" for="ca-model">모델</label>
        <input
          id="ca-model"
          type="text"
          class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
            focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
          placeholder="gemini-2.0-flash"
          bind:value={caModel}
        />
      </div>
    </div>
  {/if}

  <!-- Integrated Server Config -->
  {#if engineType === 'integrated_server'}
    <div class="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <h4 class="text-sm font-medium text-gray-700">통합 파이프라인 서버</h4>
      <div>
        <label class="block text-xs font-medium text-gray-600 mb-1" for="is-url">서버 URL</label>
        <input
          id="is-url"
          type="text"
          class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
            focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
          placeholder="http://localhost:18811"
          bind:value={isUrl}
        />
      </div>
    </div>
  {/if}

  <!-- Split Pipeline Config -->
  {#if engineType === 'split_pipeline'}
    <div class="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <h4 class="text-sm font-medium text-gray-700">레이아웃 서버</h4>
      <div>
        <label class="block text-xs font-medium text-gray-600 mb-1" for="sp-layout-url">
          레이아웃 서버 URL
        </label>
        <input
          id="sp-layout-url"
          type="text"
          class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
            focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
          placeholder="http://localhost:18811"
          bind:value={spLayoutUrl}
        />
      </div>
    </div>

    <div class="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <h4 class="text-sm font-medium text-gray-700">OCR 프로바이더</h4>
      <div class="grid grid-cols-2 gap-3 mb-3">
        <button
          type="button"
          class="text-left p-2 rounded-lg border-2 transition-all
            {spOcrProvider === 'gemini'
            ? 'border-primary-500 bg-primary-50/50'
            : 'border-gray-200 hover:border-gray-300 bg-white'}"
          onclick={() => (spOcrProvider = 'gemini')}
        >
          <div class="font-medium text-sm text-gray-900">Google Gemini</div>
        </button>
        <button
          type="button"
          class="text-left p-2 rounded-lg border-2 transition-all
            {spOcrProvider === 'vllm'
            ? 'border-primary-500 bg-primary-50/50'
            : 'border-gray-200 hover:border-gray-300 bg-white'}"
          onclick={() => (spOcrProvider = 'vllm')}
        >
          <div class="font-medium text-sm text-gray-900">vLLM</div>
        </button>
      </div>

      {#if spOcrProvider === 'gemini'}
        <div>
          <label class="block text-xs font-medium text-gray-600 mb-1" for="sp-ocr-api-key">
            API Key
          </label>
          <input
            id="sp-ocr-api-key"
            type="password"
            class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
              focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
            placeholder="Google Gemini API Key"
            bind:value={spOcrApiKey}
          />
        </div>
      {/if}

      {#if spOcrProvider === 'vllm'}
        <div class="grid grid-cols-3 gap-3">
          <div class="col-span-2">
            <label class="block text-xs font-medium text-gray-600 mb-1" for="sp-ocr-host">
              호스트
            </label>
            <input
              id="sp-ocr-host"
              type="text"
              class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
                focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
              placeholder="localhost"
              bind:value={spOcrHost}
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1" for="sp-ocr-port">
              포트
            </label>
            <input
              id="sp-ocr-port"
              type="number"
              class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
                focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
              placeholder="8000"
              min="1"
              max="65535"
              bind:value={spOcrPort}
            />
          </div>
        </div>
      {/if}

      <div>
        <label class="block text-xs font-medium text-gray-600 mb-1" for="sp-ocr-model">
          모델
        </label>
        <input
          id="sp-ocr-model"
          type="text"
          class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
            focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
          placeholder="gemini-2.0-flash"
          bind:value={spOcrModel}
        />
      </div>
    </div>
  {/if}

  <!-- Connection Test Result -->
  {#if testResult}
    <div
      class="p-3 rounded-lg text-sm border
        {testResult.success
        ? 'bg-green-50 border-green-200 text-green-700'
        : 'bg-red-50 border-red-200 text-red-700'}"
    >
      {testResult.message}
    </div>
  {/if}

  <!-- Action Buttons -->
  <div class="flex items-center justify-end gap-2">
    {#if needsConnectionTest}
      <Button variant="secondary" disabled={!isValid || testing} onclick={handleTest}>
        {testing ? '테스트 중...' : '연결 테스트'}
      </Button>
    {/if}
    <Button variant="primary" disabled={!isValid || saving} onclick={handleSave}>
      {saving ? '저장 중...' : '설정 저장'}
    </Button>
  </div>
</div>
