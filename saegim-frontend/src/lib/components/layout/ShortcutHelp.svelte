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
      label: '도구',
      items: [
        { key: '1', description: '선택' },
        { key: '2', description: '그리기' },
        { key: '3', description: '이동' },
      ],
    },
    {
      label: '편집',
      items: [
        { key: `${modKey}+S`, description: '저장' },
        { key: `${modKey}+Z`, description: '실행 취소' },
        { key: `${modKey}+Shift+Z`, description: '다시 실행' },
        { key: 'X', description: '요소 삭제' },
      ],
    },
    {
      label: '보기',
      items: [{ key: 'R', description: '읽기 순서 토글' }],
    },
    {
      label: '탐색',
      items: [
        { key: 'Q', description: '이전 페이지' },
        { key: 'E', description: '다음 페이지' },
        { key: 'Esc', description: '선택 해제' },
      ],
    },
    {
      label: '도움말',
      items: [{ key: '`', description: '이 도움말' }],
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
        <span class="sr-only">키보드 단축키</span>
      </Button>
    {/snippet}
  </Popover.Trigger>
  <Popover.Content side="bottom" align="end" class="w-64 p-3">
    <div class="mb-2 text-sm font-semibold">키보드 단축키</div>
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
