<script lang="ts">
  import { ModeWatcher } from 'mode-watcher'
  import { page } from '$app/state'
  import { goto } from '$app/navigation'
  import { authStore } from '$lib/stores/auth.svelte'
  import '../app.css'

  let { children } = $props()

  const PUBLIC_PATHS = ['/login', '/register']

  function isPublicRoute(pathname: string): boolean {
    return PUBLIC_PATHS.some((p) => pathname.startsWith(p))
  }

  // Redirect to /login when not authenticated on protected routes
  $effect(() => {
    if (!authStore.isAuthenticated && !isPublicRoute(page.url.pathname)) {
      goto('/login')
    }
  })

  // Periodically check token expiration (triggers auto-logout via $effect above)
  $effect(() => {
    const interval = setInterval(() => {
      authStore.checkExpiration()
    }, 60_000)

    return () => clearInterval(interval)
  })
</script>

<ModeWatcher />
<div class="bg-background text-foreground flex h-full flex-col">
  {#if authStore.isAuthenticated || isPublicRoute(page.url.pathname)}
    {@render children()}
  {/if}
</div>
