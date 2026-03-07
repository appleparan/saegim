<script lang="ts">
  import { goto } from '$app/navigation'
  import { authStore } from '$lib/stores/auth.svelte'
  import { checkLoginId, register } from '$lib/api/auth'
  import { ApiError } from '$lib/api/client'
  import { Button } from '$lib/components/ui/button'
  import { Input } from '$lib/components/ui/input'
  import { Label } from '$lib/components/ui/label'
  import * as Card from '$lib/components/ui/card'

  let name = $state('')
  let loginId = $state('')
  let password = $state('')
  let passwordConfirm = $state('')
  let error = $state<string | null>(null)
  let isSubmitting = $state(false)
  let loginIdStatus = $state<'idle' | 'invalid' | 'checking' | 'available' | 'taken'>('idle')
  let loginIdHint = $derived.by(() => {
    if (loginIdStatus === 'invalid') return 'ID는 3자 이상이어야 합니다.'
    if (loginIdStatus === 'checking') return 'ID 중복 확인 중입니다...'
    if (loginIdStatus === 'available') return '사용 가능한 ID입니다.'
    if (loginIdStatus === 'taken') return '이미 사용 중인 ID입니다.'
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
    const trimmedName = name.trim()
    const trimmedLoginId = loginId.trim()

    if (!trimmedName || !trimmedLoginId || !password) return

    if (password !== passwordConfirm) {
      error = '비밀번호가 일치하지 않습니다.'
      return
    }

    if (password.length < 8) {
      error = '비밀번호는 최소 8자 이상이어야 합니다.'
      return
    }

    if (trimmedLoginId.length < 3) {
      error = 'ID는 3자 이상이어야 합니다.'
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
        error = '이미 사용 중인 ID입니다.'
        return
      }

      const response = await register({
        name: trimmedName,
        login_id: trimmedLoginId,
        password,
      })
      authStore.setToken(response.access_token)
      await goto('/')
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        error = '이미 사용 중인 ID입니다.'
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
          <Label for="login-id">ID</Label>
          <Input
            id="login-id"
            type="text"
            placeholder="사용할 ID"
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
