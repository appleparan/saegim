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
    if (loginIdStatus === 'invalid') return 'ID는 3자 이상이어야 합니다.'
    if (loginIdStatus === 'checking') return 'ID 중복 확인 중입니다...'
    if (loginIdStatus === 'available') return '사용 가능한 ID입니다.'
    if (loginIdStatus === 'taken') return '이미 사용 중인 ID입니다.'
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
        if (detail.includes('login ID')) return '이미 사용 중인 ID입니다.'
        if (detail.includes('email')) return '이미 사용 중인 이메일입니다.'
        return detail
      }
    }
    return '계정 정보 변경 중 오류가 발생했습니다. 다시 시도해 주세요.'
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
      error = '변경할 항목(ID, 이메일, 비밀번호) 중 하나 이상을 입력해 주세요.'
      return
    }

    if (authStore.mustChangePassword && !hasPassword) {
      error = '초기 계정은 비밀번호를 반드시 변경해야 합니다.'
      return
    }

    if (hasPassword && newPassword !== newPasswordConfirm) {
      error = '새 비밀번호와 비밀번호 확인이 일치하지 않습니다.'
      return
    }
    if (hasPassword && newPassword.length < 8) {
      error = '새 비밀번호는 최소 8자 이상이어야 합니다.'
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
        error = '이미 사용 중인 ID입니다.'
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
      success = '계정 정보가 변경되었습니다.'
      await goto('/')
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        error = '현재 비밀번호가 올바르지 않습니다.'
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
      <Card.Title class="text-2xl font-bold">계정 보안 설정</Card.Title>
      <Card.Description>ID / 이메일 / 비밀번호를 변경할 수 있습니다.</Card.Description>
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
          <Label for="current-password">현재 비밀번호</Label>
          <Input
            id="current-password"
            type="password"
            bind:value={currentPassword}
            required
            autocomplete="current-password"
          />
        </div>

        <div class="space-y-2">
          <Label for="new-login-id">새 ID (선택)</Label>
          <Input
            id="new-login-id"
            type="text"
            bind:value={newLoginId}
            placeholder="변경할 ID"
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
          <Label for="new-email">새 이메일 (선택)</Label>
          <Input id="new-email" type="email" bind:value={newEmail} placeholder="new@example.com" />
        </div>

        <div class="space-y-2">
          <Label for="new-password">새 비밀번호 (선택)</Label>
          <Input id="new-password" type="password" bind:value={newPassword} minlength={8} />
        </div>

        <div class="space-y-2">
          <Label for="new-password-confirm">새 비밀번호 확인</Label>
          <Input
            id="new-password-confirm"
            type="password"
            bind:value={newPasswordConfirm}
            minlength={8}
          />
        </div>

        <Button type="submit" class="w-full" disabled={isSubmitting}>
          {isSubmitting ? '변경 중...' : '계정 정보 변경'}
        </Button>
      </form>
    </Card.Content>
  </Card.Root>
</div>
