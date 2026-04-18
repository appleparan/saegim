<script lang="ts">
  import { goto } from '$app/navigation'
  import { authStore } from '$lib/stores/auth.svelte'
  import { checkLoginId, register } from '$lib/api/auth'
  import { ApiError } from '$lib/api/client'
  import { Button } from '$lib/components/ui/button'
  import { Input } from '$lib/components/ui/input'
  import { Label } from '$lib/components/ui/label'
  import * as Card from '$lib/components/ui/card'
  import AuthHero from '$lib/components/layout/AuthHero.svelte'

  let loginId = $state('')
  let password = $state('')
  let passwordConfirm = $state('')
  let name = $state('')
  let email = $state('')
  let error = $state<string | null>(null)
  let isSubmitting = $state(false)
  let loginIdStatus = $state<'idle' | 'invalid' | 'checking' | 'available' | 'taken'>('idle')
  let loginIdHint = $derived.by(() => {
    if (loginIdStatus === 'invalid') return 'ID must be at least 3 characters.'
    if (loginIdStatus === 'checking') return 'Checking ID availability...'
    if (loginIdStatus === 'available') return 'ID is available.'
    if (loginIdStatus === 'taken') return 'ID is already in use.'
    return null
  })

  $effect(() => {
    if (authStore.isAuthenticated) {
      goto('/')
    }
  })

  $effect(() => {
    const trimmedLoginId = loginId.trim()
    if (!trimmedLoginId) {
      loginIdStatus = 'idle'
      return
    }
    if (trimmedLoginId.length < 3) {
      loginIdStatus = 'invalid'
      return
    }

    loginIdStatus = 'checking'
    const timer = setTimeout(async () => {
      try {
        const result = await checkLoginId(trimmedLoginId)
        if (loginId.trim() !== trimmedLoginId) return
        loginIdStatus = result.available ? 'available' : 'taken'
      } catch {
        if (loginId.trim() === trimmedLoginId) {
          loginIdStatus = 'idle'
        }
      }
    }, 300)

    return () => clearTimeout(timer)
  })

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault()
    const trimmedLoginId = loginId.trim()
    const trimmedName = name.trim()
    const trimmedEmail = email.trim()

    if (!trimmedLoginId || !password || !trimmedName || !trimmedEmail) return

    if (password !== passwordConfirm) {
      error = 'Passwords do not match.'
      return
    }

    if (password.length < 8) {
      error = 'Password must be at least 8 characters.'
      return
    }

    if (trimmedLoginId.length < 3) {
      error = 'ID must be at least 3 characters.'
      return
    }

    error = null
    isSubmitting = true
    try {
      let isAvailable = loginIdStatus === 'available'
      if (!isAvailable) {
        const result = await checkLoginId(trimmedLoginId)
        isAvailable = result.available
        loginIdStatus = isAvailable ? 'available' : 'taken'
      }
      if (!isAvailable) {
        error = 'ID is already in use.'
        return
      }

      const response = await register({
        login_id: trimmedLoginId,
        password,
        name: trimmedName,
        email: trimmedEmail,
      })
      authStore.setToken(response.access_token)
      await goto('/')
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        error = 'ID or email is already in use.'
      } else {
        error = 'An error occurred while signing up. Please try again.'
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
        <Card.Description>Create a new account</Card.Description>
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
              placeholder="Choose an ID"
              bind:value={loginId}
              required
              autocomplete="username"
            />
            {#if loginIdHint}
              <p
                class="text-xs {loginIdStatus === 'taken' || loginIdStatus === 'invalid'
                  ? 'text-red-600'
                  : loginIdStatus === 'available'
                    ? 'text-emerald-600'
                    : 'text-muted-foreground'}"
              >
                {loginIdHint}
              </p>
            {/if}
          </div>

          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="At least 8 characters"
              bind:value={password}
              required
              minlength={8}
              autocomplete="new-password"
            />
          </div>

          <div class="space-y-2">
            <Label for="password-confirm">Confirm Password</Label>
            <Input
              id="password-confirm"
              type="password"
              bind:value={passwordConfirm}
              required
              minlength={8}
              autocomplete="new-password"
            />
          </div>

          <div class="space-y-2">
            <Label for="name">Name</Label>
            <Input
              id="name"
              type="text"
              placeholder="Jane Doe"
              bind:value={name}
              required
              autocomplete="name"
            />
          </div>

          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="user@example.com"
              bind:value={email}
              required
              autocomplete="email"
            />
          </div>

          <Button type="submit" class="w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Signing up...' : 'Sign up'}
          </Button>
        </form>
      </Card.Content>
      <Card.Footer class="justify-center">
        <p class="text-muted-foreground text-sm">
          Already have an account?
          <a href="/login" class="text-primary font-medium hover:underline">Sign in</a>
        </p>
      </Card.Footer>
    </Card.Root>
  </div>
</div>
