<script lang="ts">
  import { goto } from '$app/navigation'
  import { authStore } from '$lib/stores/auth.svelte'
  import { login } from '$lib/api/auth'
  import { ApiError } from '$lib/api/client'
  import { Button } from '$lib/components/ui/button'
  import { Input } from '$lib/components/ui/input'
  import { Label } from '$lib/components/ui/label'
  import * as Card from '$lib/components/ui/card'
  import AuthHero from '$lib/components/layout/AuthHero.svelte'

  let loginId = $state('')
  let password = $state('')
  let error = $state<string | null>(null)
  let isSubmitting = $state(false)

  $effect(() => {
    if (authStore.isAuthenticated) {
      goto('/')
    }
  })

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault()
    const trimmedLoginId = loginId.trim()
    if (!trimmedLoginId || !password) return

    error = null
    isSubmitting = true
    try {
      const response = await login({ login_id: trimmedLoginId, password })
      authStore.setToken(response.access_token)
      await goto('/')
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        error = 'Invalid ID or password.'
      } else {
        error = 'An error occurred while signing in. Please try again.'
      }
    } finally {
      isSubmitting = false
    }
  }
</script>

<div class="mx-auto flex min-h-screen w-full max-w-6xl">
  <AuthHero />

  <div class="flex w-full items-center justify-center px-4 lg:w-1/2">
    <Card.Root class="w-full max-w-sm">
      <Card.Header class="text-center">
        <Card.Title class="text-2xl font-bold">saegim</Card.Title>
        <Card.Description>Sign in to your account</Card.Description>
      </Card.Header>
      <Card.Content>
        <form onsubmit={handleSubmit} class="space-y-4">
          {#if error}
            <div
              class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-800 dark:bg-red-950/50 dark:text-red-200"
            >
              {error}
            </div>
          {/if}

          <div class="space-y-2">
            <Label for="login-id">ID</Label>
            <Input
              id="login-id"
              type="text"
              placeholder="admin"
              bind:value={loginId}
              required
              autocomplete="username"
            />
          </div>

          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input
              id="password"
              type="password"
              bind:value={password}
              required
              autocomplete="current-password"
            />
          </div>

          <Button type="submit" class="w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </Button>
        </form>
      </Card.Content>
      <Card.Footer class="justify-center">
        <p class="text-muted-foreground text-sm">
          No account yet?
          <a href="/register" class="text-primary font-medium hover:underline">Sign up</a>
        </p>
      </Card.Footer>
    </Card.Root>
  </div>
</div>
