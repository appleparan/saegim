<script lang="ts">
  import { goto } from '$app/navigation'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { autosaveStore } from '$lib/stores/autosave.svelte'
  import { authStore } from '$lib/stores/auth.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import { Switch } from '$lib/components/ui/switch'
  import ClipboardList from '@lucide/svelte/icons/clipboard-list'
  import Loader from '@lucide/svelte/icons/loader'
  import LogOut from '@lucide/svelte/icons/log-out'
  import Shield from '@lucide/svelte/icons/shield'
  import User from '@lucide/svelte/icons/user'
  import ShortcutHelp from './ShortcutHelp.svelte'
  import ThemeToggle from './ThemeToggle.svelte'

  function handleLogout() {
    authStore.logout()
    goto('/login')
  }

  interface Props {
    title?: string
    showSave?: boolean
    showRevert?: boolean
    showAutoSave?: boolean
    onsave?: () => void
    onrevert?: () => void
    saving?: boolean
    reverting?: boolean
    showShortcutHelp?: boolean
    shortcutHelpOpen?: boolean
  }

  let {
    title = 'saegim',
    showSave = false,
    showRevert = false,
    showAutoSave = false,
    onsave,
    onrevert,
    saving = false,
    reverting = false,
    showShortcutHelp = false,
    shortcutHelpOpen = $bindable(false),
  }: Props = $props()

  function formatTime(date: Date): string {
    return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
  }
</script>

<header class="flex h-12 shrink-0 items-center bg-zinc-900 px-4 shadow-sm dark:bg-zinc-950">
  <div class="flex items-center gap-4">
    <a href="/" class="text-base font-bold text-white transition-colors hover:text-violet-300">
      {title}
    </a>
  </div>

  <div class="flex-1"></div>

  <div class="flex items-center gap-3">
    {#if showAutoSave}
      <div class="flex items-center gap-2">
        <label class="flex cursor-pointer items-center gap-1.5">
          <span class="text-xs font-medium text-white/70">자동 저장</span>
          <Switch
            checked={autosaveStore.enabled}
            onCheckedChange={(checked) => autosaveStore.setEnabled(checked)}
          />
        </label>
        {#if autosaveStore.enabled && autosaveStore.isSaving}
          <Loader class="size-3.5 animate-spin text-white/50" />
        {/if}
        {#if autosaveStore.enabled && autosaveStore.lastSavedAt && !autosaveStore.isSaving}
          <span class="text-[11px] text-white/40">{formatTime(autosaveStore.lastSavedAt)}</span>
        {/if}
      </div>
      <div class="mx-1 h-5 w-px bg-white/20"></div>
    {/if}

    {#if annotationStore.isDirty}
      <span
        class="inline-flex items-center rounded-full border border-amber-500/30 bg-amber-500/20 px-2 py-0.5 text-xs font-medium text-amber-300"
      >
        저장되지 않은 변경
      </span>
    {/if}

    {#if showSave}
      {#if showRevert}
        <button
          class="rounded-lg border border-white/20 px-3 py-1.5 text-sm font-medium text-white/85 transition-all
            {reverting || !annotationStore.isDirty
            ? 'cursor-not-allowed bg-white/5 text-white/30'
            : 'hover:bg-white/10 active:bg-white/15'}"
          disabled={reverting || !annotationStore.isDirty}
          onclick={onrevert}
        >
          {reverting ? '되돌리는 중...' : '마지막 저장으로 되돌리기'}
        </button>
      {/if}

      <button
        class="rounded-lg px-3 py-1.5 text-sm font-medium transition-all
          {saving || !annotationStore.isDirty
          ? 'cursor-not-allowed bg-white/10 text-white/40'
          : 'bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/80 shadow-sm'}"
        disabled={saving || !annotationStore.isDirty}
        onclick={onsave}
      >
        {saving ? '저장 중...' : '저장'}
      </button>
    {/if}

    {#if showShortcutHelp}
      <ShortcutHelp bind:open={shortcutHelpOpen} />
    {/if}

    {#if authStore.isAuthenticated}
      <a
        href="/account/security"
        class="flex items-center gap-1 rounded-lg px-2 py-1.5 text-sm font-medium text-white/80 transition-colors hover:bg-white/10 hover:text-white"
      >
        <User class="size-4" />
        <span>계정</span>
      </a>
    {/if}

    {#if authStore.isAuthenticated}
      <a
        href="/tasks"
        class="flex items-center gap-1 rounded-lg px-2 py-1.5 text-sm font-medium text-white/80 transition-colors hover:bg-white/10 hover:text-white"
      >
        <ClipboardList class="size-4" />
        <span>내 작업</span>
      </a>
    {/if}

    {#if authStore.isAdmin}
      <a
        href="/admin"
        class="flex items-center gap-1 rounded-lg px-2 py-1.5 text-sm font-medium text-white/80 transition-colors hover:bg-white/10 hover:text-white"
      >
        <Shield class="size-4" />
        <span>관리</span>
      </a>
    {/if}

    <ThemeToggle />

    {#if authStore.isAuthenticated}
      <button
        class="flex items-center gap-1 rounded-lg px-2 py-1.5 text-sm font-medium text-white/80 transition-colors hover:bg-white/10 hover:text-white"
        onclick={handleLogout}
      >
        <LogOut class="size-4" />
        <span>로그아웃</span>
      </button>
    {/if}
  </div>

  {#if uiStore.notification}
    <div
      class="fixed top-4 right-4 z-50 rounded-xl border px-4 py-3 text-sm shadow-lg
        {uiStore.notification.type === 'error'
        ? 'border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950/50 dark:text-red-200'
        : uiStore.notification.type === 'success'
          ? 'border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950/50 dark:text-green-200'
          : 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-950/50 dark:text-blue-200'}"
    >
      {uiStore.notification.message}
    </div>
  {/if}
</header>
