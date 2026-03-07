<script lang="ts">
  import { Switch } from '$lib/components/ui/switch'
  import type { AdminUserResponse, UserRole } from '$lib/api/types'

  interface Props {
    users: readonly AdminUserResponse[]
    onrolechange?: (userId: string, role: UserRole) => void
    ontoggleactive?: (userId: string, isActive: boolean) => void
  }

  let { users, onrolechange, ontoggleactive }: Props = $props()

  const ROLE_LABELS: Record<UserRole, string> = {
    admin: '관리자',
    annotator: '주석자',
    reviewer: '검수자',
  }

  const ROLE_COLORS: Record<UserRole, string> = {
    admin: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
    annotator: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    reviewer: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  }

  const ROLE_OPTIONS: UserRole[] = ['admin', 'annotator', 'reviewer']

  function handleRoleChange(userId: string, newRole: string) {
    onrolechange?.(userId, newRole as UserRole)
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('ko-KR')
  }
</script>

<div class="space-y-4">
  <div>
    <h3 class="text-foreground text-sm font-semibold">사용자 관리</h3>
    <p class="text-muted-foreground text-xs">시스템 사용자를 관리하고 역할을 변경하세요.</p>
  </div>

  {#if users.length > 0}
    <div class="border-border overflow-hidden rounded-lg border">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-muted/50 border-border border-b">
            <th class="text-muted-foreground px-4 py-2 text-left font-medium">이름</th>
            <th class="text-muted-foreground px-4 py-2 text-left font-medium">로그인 ID</th>
            <th class="text-muted-foreground px-4 py-2 text-left font-medium">이메일</th>
            <th class="text-muted-foreground px-4 py-2 text-left font-medium">역할</th>
            <th class="text-muted-foreground px-4 py-2 text-center font-medium">활성화</th>
            <th class="text-muted-foreground px-4 py-2 text-left font-medium">가입일</th>
          </tr>
        </thead>
        <tbody>
          {#each users as user (user.id)}
            <tr class="border-border border-b last:border-b-0">
              <td class="text-foreground px-4 py-3 font-medium">{user.name}</td>
              <td class="text-muted-foreground px-4 py-3">{user.login_id}</td>
              <td class="text-muted-foreground px-4 py-3">{user.email}</td>
              <td class="px-4 py-3">
                {#if onrolechange}
                  <select
                    class="border-input bg-background text-foreground focus:border-ring
                      focus:ring-ring rounded-md border px-2 py-1 text-xs focus:ring-1"
                    value={user.role}
                    onchange={(e) => handleRoleChange(user.id, e.currentTarget.value)}
                  >
                    {#each ROLE_OPTIONS as role}
                      <option value={role}>{ROLE_LABELS[role]}</option>
                    {/each}
                  </select>
                {:else}
                  <span
                    class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium {ROLE_COLORS[user.role]}"
                  >
                    {ROLE_LABELS[user.role]}
                  </span>
                {/if}
              </td>
              <td class="px-4 py-3 text-center">
                <Switch
                  checked={user.is_active}
                  onCheckedChange={(checked) => ontoggleactive?.(user.id, checked)}
                />
              </td>
              <td class="text-muted-foreground px-4 py-3">{formatDate(user.created_at)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <div class="border-border rounded-lg border border-dashed p-8 text-center">
      <p class="text-muted-foreground text-sm">등록된 사용자가 없습니다.</p>
    </div>
  {/if}
</div>
