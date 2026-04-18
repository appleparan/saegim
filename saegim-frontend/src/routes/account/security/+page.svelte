<script lang="ts">
  import { goto } from '$app/navigation'
  import { ApiError } from '$lib/api/client'
  import { checkLoginId, updateMyCredentials } from '$lib/api/auth'
  import { authStore } from '$lib/stores/auth.svelte'
  import { Button } from '$lib/components/ui/button'
  import { Input } from '$lib/components/ui/input'
  import { Label } from '$lib/components/ui/label'
  import * as Card from '$lib/components/ui/card'

  let currentPassword = $state('')
  let newLoginId = $state('')
  let newEmail = $state('')
  let newPassword = $state('')
  let newPasswordConfirm = $state('')
  let error = $state<string | null>(null)
  let success = $state<string | null>(null)
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
    const trimmed = newLoginId.trim()
    if (!trimmed) {
      loginIdStatus = 'idle'
      return
    }
    if (trimmed.length < 3) {
      loginIdStatus = 'invalid'
      return
    }

    loginIdStatus = 'checking'
    const timer = setTimeout(async () => {
      try {
        const result = await checkLoginId(trimmed)
        if (newLoginId.trim() !== trimmed) return
        loginIdStatus = result.available ? 'available' : 'taken'
      } catch {
        if (newLoginId.trim() === trimmed) {
          loginIdStatus = 'idle'
        }
      }
    }, 300)
    return () => clearTimeout(timer)
  })

  function parseErrorMessage(err: unknown): string {
    if (err instanceof ApiError && err.body && typeof err.body === 'object' && 'detail' in err.body) {
      const detail = (err.body as { detail: unknown }).detail
      if (typeof detail === 'string') {
        if (detail.includes('login ID')) return 'ID is already in use.'
        if (detail.includes('email')) return 'Email is already in use.'
        return detail
      }
    }
    return 'An error occurred while updating account information. Please try again.'
  }

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault()

    const trimmedLoginId = newLoginId.trim()
    const trimmedEmail = newEmail.trim()
    const hasLoginId = trimmedLoginId.length > 0
    const hasEmail = trimmedEmail.length > 0
    const hasPassword = newPassword.length > 0

    if (!currentPassword) return
    if (!hasLoginId && !hasEmail && !hasPassword) {
      error = 'Enter at least one field to update: ID, email, or password.'
      return
    }

    if (authStore.mustChangePassword && !hasPassword) {
      error = 'The initial account must change its password.'
      return
    }

    if (hasPassword && newPassword !== newPasswordConfirm) {
      error = 'New password and confirmation do not match.'
      return
    }
    if (hasPassword && newPassword.length < 8) {
      error = 'New password must be at least 8 characters.'
      return
    }

    if (hasLoginId) {
      let available = loginIdStatus === 'available'
      if (!available) {
        const result = await checkLoginId(trimmedLoginId)
        available = result.available
        loginIdStatus = available ? 'available' : 'taken'
      }
      if (!available) {
        error = 'ID is already in use.'
        return
      }
    }

    error = null
    success = null
    isSubmitting = true
    try {
      const response = await updateMyCredentials({
        current_password: currentPassword,
        login_id: hasLoginId ? trimmedLoginId : undefined,
        email: hasEmail ? trimmedEmail : undefined,
        new_password: hasPassword ? newPassword : undefined,
      })

      authStore.setToken(response.access_token)
      success = 'Account information updated.'
      await goto('/')
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        error = 'Current password is incorrect.'
      } else {
        error = parseErrorMessage(err)
      }
    } finally {
      isSubmitting = false
    }
  }
</script>

<div class="flex min-h-screen items-center justify-center px-4">
  <Card.Root class="w-full max-w-md">
    <Card.Header class="text-center">
      <Card.Title class="text-2xl font-bold">Account Security Settings</Card.Title>
      <Card.Description>Update your ID, email, or password.</Card.Description>
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

        {#if success}
          <div
            class="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200"
          >
            {success}
          </div>
        {/if}

        <div class="space-y-2">
          <Label for="current-password">Current Password</Label>
          <Input
            id="current-password"
            type="password"
            bind:value={currentPassword}
            required
            autocomplete="current-password"
          />
        </div>

        <div class="space-y-2">
          <Label for="new-login-id">New ID (Optional)</Label>
          <Input
            id="new-login-id"
            type="text"
            bind:value={newLoginId}
            placeholder="New ID"
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
          <Label for="new-email">New Email (Optional)</Label>
          <Input id="new-email" type="email" bind:value={newEmail} placeholder="new@example.com" />
        </div>

        <div class="space-y-2">
          <Label for="new-password">New Password (Optional)</Label>
          <Input id="new-password" type="password" bind:value={newPassword} minlength={8} />
        </div>

        <div class="space-y-2">
          <Label for="new-password-confirm">Confirm New Password</Label>
          <Input
            id="new-password-confirm"
            type="password"
            bind:value={newPasswordConfirm}
            minlength={8}
          />
        </div>

        <Button type="submit" class="w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Updating...' : 'Update Account'}
        </Button>
      </form>
    </Card.Content>
  </Card.Root>
</div>
