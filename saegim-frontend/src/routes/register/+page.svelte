<script lang="ts">
  import { goto } from '$app/navigation'
  import { authStore } from '$lib/stores/auth.svelte'
  import { register } from '$lib/api/auth'
  import { ApiError } from '$lib/api/client'
  import { Button } from '$lib/components/ui/button'
  import { Input } from '$lib/components/ui/input'
  import { Label } from '$lib/components/ui/label'
  import * as Card from '$lib/components/ui/card'

  let name = $state('')
  let email = $state('')
  let password = $state('')
  let passwordConfirm = $state('')
  let error = $state<string | null>(null)
  let isSubmitting = $state(false)

  $effect(() => {
    if (authStore.isAuthenticated) {
      goto('/')
    }
  })

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault()
    const trimmedName = name.trim()
    const trimmedEmail = email.trim()

    if (!trimmedName || !trimmedEmail || !password) return

    if (password !== passwordConfirm) {
      error = '비밀번호가 일치하지 않습니다.'
      return
    }

    if (password.length < 8) {
      error = '비밀번호는 최소 8자 이상이어야 합니다.'
      return
    }

    error = null
    isSubmitting = true
    try {
      const response = await register({
        name: trimmedName,
        email: trimmedEmail,
        password,
      })
      authStore.setToken(response.access_token)
      await goto('/')
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        error = '이미 사용 중인 이메일입니다.'
      } else {
        error = '회원가입 중 오류가 발생했습니다. 다시 시도해 주세요.'
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
      <Card.Description>새 계정을 만드세요</Card.Description>
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
          <Label for="name">이름</Label>
          <Input
            id="name"
            type="text"
            placeholder="홍길동"
            bind:value={name}
            required
            autocomplete="name"
          />
        </div>

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
            placeholder="최소 8자"
            bind:value={password}
            required
            minlength={8}
            autocomplete="new-password"
          />
        </div>

        <div class="space-y-2">
          <Label for="password-confirm">비밀번호 확인</Label>
          <Input
            id="password-confirm"
            type="password"
            bind:value={passwordConfirm}
            required
            minlength={8}
            autocomplete="new-password"
          />
        </div>

        <Button type="submit" class="w-full" disabled={isSubmitting}>
          {isSubmitting ? '가입 중...' : '회원가입'}
        </Button>
      </form>
    </Card.Content>
    <Card.Footer class="justify-center">
      <p class="text-muted-foreground text-sm">
        이미 계정이 있으신가요?
        <a href="/login" class="text-primary font-medium hover:underline">로그인</a>
      </p>
    </Card.Footer>
  </Card.Root>
</div>
