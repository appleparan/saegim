<script lang="ts">
  import { Button } from '$lib/components/ui/button'
  import * as Dialog from '$lib/components/ui/dialog'
  import type { ProjectMemberRole } from '$lib/api/types'
  import type { UserListItem } from '$lib/api/users'

  interface Props {
    open: boolean
    users: readonly UserListItem[]
    onadd?: (userId: string, role: ProjectMemberRole) => void
  }

  let { open = $bindable(false), users, onadd }: Props = $props()

  let selectedUserId = $state('')
  let selectedRole = $state<ProjectMemberRole>('annotator')
  let searchQuery = $state('')

  let filteredUsers = $derived(
    searchQuery.trim()
      ? users.filter(
          (u) =>
            u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            u.email.toLowerCase().includes(searchQuery.toLowerCase()),
        )
      : users,
  )

  let isValid = $derived(selectedUserId.length > 0)

  function reset() {
    selectedUserId = ''
    selectedRole = 'annotator'
    searchQuery = ''
  }

  function handleOpenChange(next: boolean) {
    if (!next) reset()
    open = next
  }

  function handleAdd() {
    if (!isValid) return
    onadd?.(selectedUserId, selectedRole)
    handleOpenChange(false)
  }
</script>

<Dialog.Root bind:open onOpenChange={handleOpenChange}>
  <Dialog.Content class="sm:max-w-md">
    <Dialog.Header>
      <Dialog.Title>멤버 추가</Dialog.Title>
      <Dialog.Description>프로젝트에 추가할 사용자를 선택하세요.</Dialog.Description>
    </Dialog.Header>

    <div class="space-y-4">
      <!-- Search -->
      <div>
        <label class="text-muted-foreground mb-1 block text-xs font-medium" for="member-search">
          사용자 검색
        </label>
        <input
          id="member-search"
          type="text"
          class="border-input bg-background text-foreground focus:border-ring focus:ring-ring
            block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
          placeholder="이름 또는 이메일로 검색..."
          bind:value={searchQuery}
        />
      </div>

      <!-- User List -->
      <div class="max-h-48 overflow-y-auto rounded-md border">
        {#if filteredUsers.length > 0}
          {#each filteredUsers as user (user.id)}
            <button
              type="button"
              class="border-border hover:bg-muted/50 flex w-full items-center gap-3
                border-b px-3 py-2 text-left last:border-b-0 transition-colors
                {selectedUserId === user.id ? 'bg-primary/10 border-primary/30' : ''}"
              onclick={() => (selectedUserId = user.id)}
            >
              <div
                class="bg-muted text-muted-foreground flex h-8 w-8
                  shrink-0 items-center justify-center rounded-full text-xs font-medium"
              >
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div class="min-w-0 flex-1">
                <div class="text-foreground truncate text-sm font-medium">{user.name}</div>
                <div class="text-muted-foreground truncate text-xs">{user.email}</div>
              </div>
              {#if selectedUserId === user.id}
                <svg
                  class="text-primary h-4 w-4 shrink-0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              {/if}
            </button>
          {/each}
        {:else}
          <div class="text-muted-foreground p-4 text-center text-sm">
            {searchQuery.trim() ? '검색 결과가 없습니다.' : '추가할 수 있는 사용자가 없습니다.'}
          </div>
        {/if}
      </div>

      <!-- Role Selection -->
      <div>
        <label class="text-muted-foreground mb-1 block text-xs font-medium" for="member-role">
          역할
        </label>
        <select
          id="member-role"
          class="border-input bg-background text-foreground focus:border-ring focus:ring-ring
            block w-full rounded-md border px-3 py-2 text-sm focus:ring-1"
          bind:value={selectedRole}
        >
          <option value="annotator">Annotator</option>
          <option value="reviewer">Reviewer</option>
        </select>
      </div>

      <Dialog.Footer>
        <Button variant="outline" onclick={() => handleOpenChange(false)}>취소</Button>
        <Button variant="default" disabled={!isValid} onclick={handleAdd}>추가</Button>
      </Dialog.Footer>
    </div>
  </Dialog.Content>
</Dialog.Root>
