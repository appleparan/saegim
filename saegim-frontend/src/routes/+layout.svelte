<script lang="ts">
  import { onMount } from 'svelte'
  import { ModeWatcher } from 'mode-watcher'
  import { page } from '$app/state'
  import { goto } from '$app/navigation'
  import { authStore } from '$lib/stores/auth.svelte'
  import '../app.css'

  let { children } = $props()

  const PUBLIC_PATHS = ['/login', '/register']
  const FORCE_CHANGE_PATH = '/account/security'

  function isPublicRoute(pathname: string): boolean {
    return PUBLIC_PATHS.some((p) => pathname.startsWith(p))
  }

  // Initialize auth state on app load (silent refresh via HttpOnly cookie)
  onMount(() => {
    authStore.initialize()
  })

  // Redirect to /login when not authenticated on protected routes
  $effect(() => {
    if (!authStore.isInitialized) return

    if (!authStore.isAuthenticated && !isPublicRoute(page.url.pathname)) {
      goto('/login')
    }

    if (
      authStore.isAuthenticated &&
      authStore.mustChangePassword &&
      !page.url.pathname.startsWith(FORCE_CHANGE_PATH)
    ) {
      goto(FORCE_CHANGE_PATH)
    }
  })

  // Proactive refresh: check every 60s and refresh if token expires within 2 min
  $effect(() => {
    const interval = setInterval(() => {
      if (authStore.shouldRefresh()) {
        authStore.refreshToken()
      }
      authStore.checkExpiration()
    }, 60_000)

    return () => clearInterval(interval)
  })
</script>

<ModeWatcher />
<div class="bg-background text-foreground flex h-full flex-col">
  {#if !authStore.isInitialized}
    <div class="flex h-screen items-center justify-center">
      <div
        class="border-primary h-8 w-8 animate-spin rounded-full border-4 border-t-transparent"
      ></div>
    </div>
  {:else if authStore.isAuthenticated || isPublicRoute(page.url.pathname)}
    {@render children()}
  {/if}
</div>
