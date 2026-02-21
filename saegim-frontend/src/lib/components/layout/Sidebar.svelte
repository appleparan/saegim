<script lang="ts">
  import type { PanelTab } from '$lib/stores/ui.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import AttributePanel from '$lib/components/panels/AttributePanel.svelte'
  import PageAttributePanel from '$lib/components/panels/PageAttributePanel.svelte'
  import TextEditor from '$lib/components/panels/TextEditor.svelte'

  const tabs: { key: PanelTab; label: string }[] = [
    { key: 'elements', label: '요소' },
    { key: 'attributes', label: '속성' },
    { key: 'text', label: '텍스트' },
  ]
</script>

{#if uiStore.sidebarOpen}
  <div class="w-80 border-l border-border bg-card flex flex-col overflow-hidden">
    <!-- Tab navigation -->
    <div class="flex border-b border-border bg-muted px-1 pt-1">
      {#each tabs as tab}
        <button
          class="flex-1 px-3 py-2 text-xs font-medium transition-all rounded-t-lg
            {uiStore.activePanel === tab.key
              ? 'text-primary bg-card border-b-2 border-primary shadow-sm'
              : 'text-muted-foreground hover:text-accent-foreground hover:bg-accent'}"
          onclick={() => uiStore.setActivePanel(tab.key)}
        >
          {tab.label}
        </button>
      {/each}
    </div>

    <!-- Panel content -->
    <div class="flex-1 overflow-y-auto">
      {#if uiStore.activePanel === 'elements'}
        <AttributePanel />
      {:else if uiStore.activePanel === 'attributes'}
        <PageAttributePanel />
      {:else if uiStore.activePanel === 'text'}
        <TextEditor />
      {/if}
    </div>
  </div>
{/if}
