<script lang="ts">
  import { ModeWatcher } from 'mode-watcher'
  import '../app.css'

  let { children } = $props()
</script>

<ModeWatcher />
<div class="h-full flex flex-col bg-background text-foreground">
  {@render children()}
</div>
