<script lang="ts">
  import { goto } from '$app/navigation'
  import { authStore } from '$lib/stores/auth.svelte'
  import { login } from '$lib/api/auth'
  import { ApiError } from '$lib/api/client'
  import { Button } from '$lib/components/ui/button'
  import { Input } from '$lib/components/ui/input'
  import { Label } from '$lib/components/ui/label'
  import * as Card from '$lib/components/ui/card'

  let email = $state('')
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
    const trimmedEmail = email.trim()
    if (!trimmedEmail || !password) return

    error = null
    isSubmitting = true
    try {
      const response = await login({ email: trimmedEmail, password })
      authStore.setToken(response.access_token)
      await goto('/')
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        error = '이메일 또는 비밀번호가 올바르지 않습니다.'
      } else {
        error = '로그인 중 오류가 발생했습니다. 다시 시도해 주세요.'
      }
    } finally {
      isSubmitting = false
    }
  }
</script>

<div class="flex min-h-screen items-center justify-center px-4">
  <Card.Root class="w-full max-w-sm">
    <Card.Header class="text-center">
      <Card.Title class="text-2xl font-bold">saegim</Card.Title>
      <Card.Description>계정에 로그인하세요</Card.Description>
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
          <Label for="email">이메일</Label>
          <Input
            id="email"
            type="email"
            placeholder="name@example.com"
            bind:value={email}
            required
            autocomplete="email"
          />
        </div>

        <div class="space-y-2">
          <Label for="password">비밀번호</Label>
          <Input
            id="password"
            type="password"
            bind:value={password}
            required
            autocomplete="current-password"
          />
        </div>

        <Button type="submit" class="w-full" disabled={isSubmitting}>
          {isSubmitting ? '로그인 중...' : '로그인'}
        </Button>
      </form>
    </Card.Content>
    <Card.Footer class="justify-center">
      <p class="text-muted-foreground text-sm">
        계정이 없으신가요?
        <a href="/register" class="text-primary font-medium hover:underline">회원가입</a>
      </p>
    </Card.Footer>
  </Card.Root>
</div>
