<script lang="ts">
  import { Button } from '$lib/components/ui/button'
  import * as Dialog from '$lib/components/ui/dialog'
  import type { EngineInstanceCreate, RegisterableEngineType } from '$lib/api/types'

  interface Props {
    open: boolean
    onOpenChange?: (open: boolean) => void
    onadd?: (data: EngineInstanceCreate) => void
    envGeminiApiKey?: string
  }

  let { open = $bindable(false), onOpenChange, onadd, envGeminiApiKey = '' }: Props = $props()

  let step = $state<'type' | 'config'>('type')
  let engineType = $state<RegisterableEngineType>('commercial_api')
  let name = $state('')

  // Commercial API config
  let caApiKey = $state('')
  let caModel = $state('gemini-3-flash-preview')
  let caPrompt = $state('')

  // vLLM config
  let vllmHost = $state('localhost')
  let vllmPort = $state(8000)
  let vllmModel = $state('')

  // Split pipeline config
  let spDoclingModel = $state('ibm-granite/granite-docling-258M')
  let spOcrProvider = $state<'gemini' | 'vllm'>('gemini')

  const ENGINE_OPTIONS: { value: RegisterableEngineType; label: string; description: string }[] = [
    {
      value: 'commercial_api',
      label: 'Gemini API',
      description: 'Google Gemini VLM OCR',
    },
    {
      value: 'vllm',
      label: 'vLLM',
      description: 'vLLM 호환 서버',
    },
    {
      value: 'split_pipeline',
      label: 'Docling + OCR',
      description: 'Docling 레이아웃 + OCR',
    },
  ]

  function reset() {
    step = 'type'
    engineType = 'commercial_api'
    name = ''
    caApiKey = ''
    caModel = 'gemini-3-flash-preview'
    caPrompt = ''
    vllmHost = 'localhost'
    vllmPort = 8000
    vllmModel = ''
    spDoclingModel = 'ibm-granite/granite-docling-258M'
    spOcrProvider = 'gemini'
  }

  function handleOpenChange(next: boolean) {
    if (!next) reset()
    open = next
    onOpenChange?.(next)
  }

  function handleSelectType(t: RegisterableEngineType) {
    engineType = t
    // Pre-fill name based on type
    if (t === 'commercial_api') name = 'Gemini Flash'
    else if (t === 'vllm') name = 'vLLM'
    else if (t === 'split_pipeline') name = 'Docling + OCR'
    // Pre-fill API key from env if available
    if (t === 'commercial_api' && envGeminiApiKey) {
      caApiKey = envGeminiApiKey
    }
    step = 'config'
  }

  function buildConfig(): Record<string, unknown> {
    if (engineType === 'commercial_api') {
      return {
        provider: 'gemini',
        api_key: caApiKey.trim(),
        model: caModel.trim(),
        prompt: caPrompt.trim(),
      }
    }
    if (engineType === 'vllm') {
      return {
        host: vllmHost.trim(),
        port: vllmPort,
        model: vllmModel.trim(),
      }
    }
    // split_pipeline
    return {
      docling_model_name: spDoclingModel.trim(),
      ocr_provider: spOcrProvider,
    }
  }

  let isValid = $derived.by(() => {
    if (!name.trim()) return false
    if (engineType === 'commercial_api') return caApiKey.trim().length > 0
    if (engineType === 'vllm') return vllmHost.trim().length > 0 && vllmPort > 0
    if (engineType === 'split_pipeline') return spDoclingModel.trim().length > 0
    return false
  })

  function handleAdd() {
    if (!isValid) return
    onadd?.({
      engine_type: engineType,
      name: name.trim(),
      config: buildConfig(),
    })
    handleOpenChange(false)
  }
</script>

<Dialog.Root bind:open onOpenChange={handleOpenChange}>
  <Dialog.Content class="sm:max-w-lg">
    <Dialog.Header>
      <Dialog.Title>
        {step === 'type' ? '엔진 타입 선택' : '엔진 설정'}
      </Dialog.Title>
      <Dialog.Description>
        {step === 'type'
          ? '등록할 OCR 엔진 타입을 선택하세요.'
          : `${ENGINE_OPTIONS.find((e) => e.value === engineType)?.label} 엔진의 이름과 설정을 입력하세요.`}
      </Dialog.Description>
    </Dialog.Header>

    {#if step === 'type'}
      <div class="space-y-2">
        {#each ENGINE_OPTIONS as opt (opt.value)}
          <button
            type="button"
            class="border-border hover:border-primary hover:bg-primary/5 w-full rounded-lg border p-3 text-left transition-all"
            onclick={() => handleSelectType(opt.value)}
          >
            <div class="text-foreground text-sm font-medium">{opt.label}</div>
            <div class="text-muted-foreground text-xs">{opt.description}</div>
          </button>
        {/each}
      </div>
    {:else}
      <div class="space-y-4">
        <!-- Name -->
        <div>
          <label class="text-muted-foreground mb-1 block text-xs font-medium" for="add-name">
            이름
          </label>
          <input
            id="add-name"
            type="text"
            class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
            placeholder="표시될 이름"
            bind:value={name}
          />
        </div>

        {#if engineType === 'commercial_api'}
          <div>
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="add-apikey">
              API Key
            </label>
            <input
              id="add-apikey"
              type="password"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
              placeholder="Google Gemini API Key"
              bind:value={caApiKey}
            />
          </div>
          <div>
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="add-model">
              모델
            </label>
            <select
              id="add-model"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
              bind:value={caModel}
            >
              <option value="gemini-3-flash-preview">gemini-3-flash-preview (Flash)</option>
              <option value="gemini-3.1-pro-preview">gemini-3.1-pro-preview (Pro)</option>
            </select>
          </div>
          <div>
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="add-prompt">
              OCR 프롬프트 (선택)
            </label>
            <textarea
              id="add-prompt"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
              rows="4"
              placeholder={"비워두면 기본 레이아웃 분석 프롬프트를 사용합니다. {width}와 {height}로 이미지 크기를 참조할 수 있습니다."}
              bind:value={caPrompt}
            ></textarea>
          </div>
        {/if}

        {#if engineType === 'vllm'}
          <div class="grid grid-cols-3 gap-3">
            <div class="col-span-2">
              <label class="text-muted-foreground mb-1 block text-xs font-medium" for="add-host">
                호스트
              </label>
              <input
                id="add-host"
                type="text"
                class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
                placeholder="localhost"
                bind:value={vllmHost}
              />
            </div>
            <div>
              <label class="text-muted-foreground mb-1 block text-xs font-medium" for="add-port">
                포트
              </label>
              <input
                id="add-port"
                type="number"
                class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
                placeholder="8000"
                bind:value={vllmPort}
              />
            </div>
          </div>
          <div>
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="add-vllm-model">
              모델
            </label>
            <input
              id="add-vllm-model"
              type="text"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
              placeholder="lightonai/LightOnOCR-2-1B-bbox-soup"
              bind:value={vllmModel}
            />
          </div>
        {/if}

        {#if engineType === 'split_pipeline'}
          <div>
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="add-docling">
              Docling 모델
            </label>
            <input
              id="add-docling"
              type="text"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
              placeholder="ibm-granite/granite-docling-258M"
              bind:value={spDoclingModel}
            />
          </div>
          <div>
            <label class="text-muted-foreground mb-1 block text-xs font-medium" for="add-sp-provider">
              OCR Provider
            </label>
            <select
              id="add-sp-provider"
              class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
              bind:value={spOcrProvider}
            >
              <option value="gemini">Gemini</option>
              <option value="vllm">vLLM</option>
            </select>
          </div>
        {/if}

        <Dialog.Footer>
          <Button variant="outline" onclick={() => (step = 'type')}>뒤로</Button>
          <Button variant="default" disabled={!isValid} onclick={handleAdd}>추가</Button>
        </Dialog.Footer>
      </div>
    {/if}
  </Dialog.Content>
</Dialog.Root>
