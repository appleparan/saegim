<script lang="ts">
  import Sun from '@lucide/svelte/icons/sun'
  import Moon from '@lucide/svelte/icons/moon'
  import { toggleMode } from 'mode-watcher'
  import { Button } from '$lib/components/ui/button'
</script>

<Button onclick={toggleMode} variant="ghost" size="icon-sm" class="text-white/80 hover:text-white hover:bg-white/10">
  <Sun class="size-4 scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90" />
  <Moon class="absolute size-4 scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0" />
  <span class="sr-only">테마 전환</span>
</Button>
