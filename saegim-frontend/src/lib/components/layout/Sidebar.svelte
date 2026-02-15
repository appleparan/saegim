<script lang="ts">
  import type { Snippet } from 'svelte'
  import type { PanelTab } from '$lib/stores/ui.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'

  interface Props {
    children: Snippet
  }

  let { children }: Props = $props()

  const tabs: { key: PanelTab; label: string }[] = [
    { key: 'elements', label: '요소' },
    { key: 'attributes', label: '속성' },
    { key: 'text', label: '텍스트' },
  ]
</script>

{#if uiStore.sidebarOpen}
  <div class="w-80 border-l border-gray-200/80 bg-white flex flex-col overflow-hidden">
    <!-- Tab navigation -->
    <div class="flex border-b border-gray-100 bg-gray-50/50 px-1 pt-1">
      {#each tabs as tab}
        <button
          class="flex-1 px-3 py-2 text-xs font-medium transition-all rounded-t-lg
            {uiStore.activePanel === tab.key
              ? 'text-primary-600 bg-white border-b-2 border-primary-500 shadow-sm'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'}"
          onclick={() => uiStore.setActivePanel(tab.key)}
        >
          {tab.label}
        </button>
      {/each}
    </div>

    <!-- Panel content -->
    <div class="flex-1 overflow-y-auto">
      {@render children()}
    </div>
  </div>
{/if}
