<script lang="ts">
  import { annotationStore } from '$lib/stores/annotation.svelte'

  let element = $derived(annotationStore.selectedElement)
  let activeTab = $state<'text' | 'latex' | 'html'>('text')

  function handleTextChange(e: Event) {
    if (!element) return
    const value = (e.target as HTMLTextAreaElement).value
    annotationStore.updateElement(element.anno_id, { [activeTab]: value })
  }

  let currentValue = $derived(
    element
      ? activeTab === 'text'
        ? element.text ?? ''
        : activeTab === 'latex'
          ? element.latex ?? ''
          : element.html ?? ''
      : '',
  )

  const tabs = [
    { key: 'text' as const, label: 'Text' },
    { key: 'latex' as const, label: 'LaTeX' },
    { key: 'html' as const, label: 'HTML' },
  ]
</script>

{#if element}
  <div class="p-3 space-y-3">
    <h3 class="text-sm font-semibold text-gray-700">텍스트 편집</h3>

    <div class="flex border-b border-gray-200">
      {#each tabs as tab}
        <button
          class="px-3 py-1.5 text-xs font-medium transition-colors
            {activeTab === tab.key
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'}"
          onclick={() => (activeTab = tab.key)}
        >
          {tab.label}
        </button>
      {/each}
    </div>

    <textarea
      class="block w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm font-mono focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-y"
      rows="8"
      value={currentValue}
      oninput={handleTextChange}
      placeholder="{activeTab === 'text'
        ? '텍스트 내용을 입력하세요...'
        : activeTab === 'latex'
          ? 'LaTeX 수식을 입력하세요...'
          : 'HTML 내용을 입력하세요...'}"
    ></textarea>
  </div>
{:else}
  <div class="p-3 text-center">
    <p class="text-sm text-gray-400 py-8">요소를 선택하면 텍스트를 편집할 수 있습니다.</p>
  </div>
{/if}
