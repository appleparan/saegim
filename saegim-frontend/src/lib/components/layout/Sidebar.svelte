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
  <div class="w-80 border-l border-gray-200 bg-white flex flex-col overflow-hidden">
    <!-- Tab navigation -->
    <div class="flex border-b border-gray-200">
      {#each tabs as tab}
        <button
          class="flex-1 px-3 py-2 text-xs font-medium transition-colors
            {uiStore.activePanel === tab.key
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'}"
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
