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
        ? (element.text ?? '')
        : activeTab === 'latex'
          ? (element.latex ?? '')
          : (element.html ?? '')
      : '',
  )

  const tabs = [
    { key: 'text' as const, label: 'Text' },
    { key: 'latex' as const, label: 'LaTeX' },
    { key: 'html' as const, label: 'HTML' },
  ]
</script>

{#if element}
  <div class="space-y-3 p-3">
    <h3 class="text-foreground text-sm font-semibold">텍스트 편집</h3>

    <div class="border-border flex border-b">
      {#each tabs as tab}
        <button
          class="px-3 py-1.5 text-xs font-medium transition-colors
            {activeTab === tab.key
            ? 'text-primary border-primary border-b-2'
            : 'text-muted-foreground hover:text-accent-foreground'}"
          onclick={() => (activeTab = tab.key)}
        >
          {tab.label}
        </button>
      {/each}
    </div>

    <textarea
      class="border-input bg-background text-foreground focus:border-ring focus:ring-ring block w-full resize-y rounded-md border px-2 py-1.5 font-mono text-sm focus:ring-1"
      rows="8"
      value={currentValue}
      oninput={handleTextChange}
      placeholder={activeTab === 'text'
        ? '텍스트 내용을 입력하세요...'
        : activeTab === 'latex'
          ? 'LaTeX 수식을 입력하세요...'
          : 'HTML 내용을 입력하세요...'}
    ></textarea>
  </div>
{:else}
  <div class="p-3 text-center">
    <p class="text-muted-foreground py-8 text-sm">요소를 선택하면 텍스트를 편집할 수 있습니다.</p>
  </div>
{/if}
