<script lang="ts">
  import Button from '$lib/components/common/Button.svelte'
  import type {
    OcrConfigResponse,
    OcrConnectionTestResponse,
    OcrProvider,
  } from '$lib/api/types'

  interface Props {
    config: OcrConfigResponse
    saving?: boolean
    testing?: boolean
    testResult?: OcrConnectionTestResponse | null
    onsave?: (config: OcrConfigResponse) => void
    ontest?: (config: OcrConfigResponse) => void
  }

  let {
    config,
    saving = false,
    testing = false,
    testResult = null,
    onsave,
    ontest,
  }: Props = $props()

  // Local form state — synced from config prop via $effect
  let provider = $state<OcrProvider>('pymupdf')
  let geminiApiKey = $state('')
  let geminiModel = $state('gemini-2.0-flash')
  let vllmHost = $state('localhost')
  let vllmPort = $state(8000)
  let vllmModel = $state('Qwen/Qwen2.5-VL-72B-Instruct')

  $effect(() => {
    provider = config.provider
    geminiApiKey = config.gemini?.api_key ?? ''
    geminiModel = config.gemini?.model ?? 'gemini-2.0-flash'
    vllmHost = config.vllm?.host ?? 'localhost'
    vllmPort = config.vllm?.port ?? 8000
    vllmModel = config.vllm?.model ?? 'Qwen/Qwen2.5-VL-72B-Instruct'
  })

  let isValid = $derived(
    provider === 'pymupdf' ||
      (provider === 'gemini' && geminiApiKey.trim().length > 0) ||
      (provider === 'vllm' && vllmHost.trim().length > 0 && vllmPort > 0),
  )

  const providers: { value: OcrProvider; label: string; description: string }[] = [
    { value: 'pymupdf', label: 'PyMuPDF', description: '동기 PyMuPDF 추출 (빠름)' },
    { value: 'gemini', label: 'Google Gemini', description: 'Gemini VLM API' },
    { value: 'vllm', label: 'vLLM', description: '로컬 vLLM 서버' },
  ]

  let needsConnectionTest = $derived(
    provider === 'gemini' || provider === 'vllm',
  )

  function buildConfig(): OcrConfigResponse {
    return {
      provider,
      ...(provider === 'gemini'
        ? { gemini: { api_key: geminiApiKey.trim(), model: geminiModel.trim() } }
        : {}),
      ...(provider === 'vllm'
        ? { vllm: { host: vllmHost.trim(), port: vllmPort, model: vllmModel.trim() } }
        : {}),
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
  <!-- Provider Selection -->
  <div>
    <h3 class="text-sm font-semibold text-gray-700 mb-3">OCR 프로바이더</h3>
    <div class="grid grid-cols-2 gap-3">
      {#each providers as p}
        <button
          type="button"
          class="text-left p-3 rounded-lg border-2 transition-all
            {provider === p.value
            ? 'border-primary-500 bg-primary-50/50'
            : 'border-gray-200 hover:border-gray-300 bg-white'}"
          onclick={() => (provider = p.value)}
        >
          <div class="font-medium text-sm text-gray-900">{p.label}</div>
          <div class="text-xs text-gray-500 mt-0.5">{p.description}</div>
        </button>
      {/each}
    </div>
  </div>

  <!-- Gemini Config -->
  {#if provider === 'gemini'}
    <div class="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <h4 class="text-sm font-medium text-gray-700">Gemini 설정</h4>
      <div>
        <label class="block text-xs font-medium text-gray-600 mb-1" for="gemini-api-key">
          API Key
        </label>
        <input
          id="gemini-api-key"
          type="password"
          class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
            focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
          placeholder="Google Gemini API Key"
          bind:value={geminiApiKey}
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-600 mb-1" for="gemini-model">
          모델
        </label>
        <input
          id="gemini-model"
          type="text"
          class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
            focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
          placeholder="gemini-2.0-flash"
          bind:value={geminiModel}
        />
      </div>
    </div>
  {/if}

  <!-- vLLM Config -->
  {#if provider === 'vllm'}
    <div class="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <h4 class="text-sm font-medium text-gray-700">vLLM 설정</h4>
      <div class="grid grid-cols-3 gap-3">
        <div class="col-span-2">
          <label class="block text-xs font-medium text-gray-600 mb-1" for="vllm-host">
            호스트
          </label>
          <input
            id="vllm-host"
            type="text"
            class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
              focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
            placeholder="localhost"
            bind:value={vllmHost}
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-gray-600 mb-1" for="vllm-port">
            포트
          </label>
          <input
            id="vllm-port"
            type="number"
            class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
              focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
            placeholder="8000"
            min="1"
            max="65535"
            bind:value={vllmPort}
          />
        </div>
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-600 mb-1" for="vllm-model">
          모델
        </label>
        <input
          id="vllm-model"
          type="text"
          class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm
            focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
          placeholder="Qwen/Qwen2.5-VL-72B-Instruct"
          bind:value={vllmModel}
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
      <Button
        variant="secondary"
        disabled={!isValid || testing}
        onclick={handleTest}
      >
        {testing ? '테스트 중...' : '연결 테스트'}
      </Button>
    {/if}
    <Button variant="primary" disabled={!isValid || saving} onclick={handleSave}>
      {saving ? '저장 중...' : '설정 저장'}
    </Button>
  </div>
</div>
