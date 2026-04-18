<script lang="ts">
  import Keyboard from '@lucide/svelte/icons/keyboard'
  import { Button } from '$lib/components/ui/button'
  import * as Popover from '$lib/components/ui/popover'

  interface Props {
    open?: boolean
  }

  let { open = $bindable(false) }: Props = $props()

  import { browser } from '$app/environment'

  const isMac = browser && /Mac|iPod|iPhone|iPad/.test(navigator.userAgent)
  const modKey = isMac ? '⌘' : 'Ctrl'

  const shortcutGroups = [
    {
      label: 'Tools',
      items: [
        { key: '1', description: 'Select' },
        { key: '2', description: 'Draw' },
        { key: '3', description: 'Pan' },
      ],
    },
    {
      label: 'Edit',
      items: [
        { key: `${modKey}+S`, description: 'Save' },
        { key: `${modKey}+Z`, description: 'Undo' },
        { key: `${modKey}+Shift+Z`, description: 'Redo' },
        { key: 'X', description: 'Select Element Delete' },
      ],
    },
    {
      label: 'View',
      items: [{ key: 'R', description: 'Toggle Reading Order' }],
    },
    {
      label: 'Navigation',
      items: [
        { key: 'Q', description: 'Previous Page' },
        { key: 'E', description: 'Next Page' },
        { key: 'Esc', description: 'Clear Selection' },
      ],
    },
    {
      label: 'Help',
      items: [{ key: '`', description: 'This Help' }],
    },
  ] as const
</script>

<Popover.Root bind:open>
  <Popover.Trigger>
    {#snippet child({ props })}
      <Button
        {...props}
        variant="ghost"
        size="icon-sm"
        class="text-white/80 hover:bg-white/10 hover:text-white"
      >
        <Keyboard class="size-4" />
        <span class="sr-only">Keyboard Shortcuts</span>
      </Button>
    {/snippet}
  </Popover.Trigger>
  <Popover.Content side="bottom" align="end" class="w-64 p-3">
    <div class="mb-2 text-sm font-semibold">Keyboard Shortcuts</div>
    <div class="space-y-3">
      {#each shortcutGroups as group}
        <div>
          <div class="text-muted-foreground mb-1 text-xs font-medium uppercase tracking-wider">
            {group.label}
          </div>
          <div class="space-y-0.5">
            {#each group.items as item}
              <div class="flex items-center justify-between py-0.5">
                <span class="text-sm">{item.description}</span>
                <kbd
                  class="bg-muted text-muted-foreground inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded border px-1.5 font-mono text-[11px] font-medium"
                >
                  {item.key}
                </kbd>
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  </Popover.Content>
</Popover.Root>
