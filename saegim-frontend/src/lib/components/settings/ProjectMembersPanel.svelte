<script lang="ts">
  import { Button } from '$lib/components/ui/button'
  import AddMemberDialog from './AddMemberDialog.svelte'
  import type { ProjectMemberResponse, ProjectMemberRole } from '$lib/api/types'
  import type { UserListItem } from '$lib/api/users'

  interface Props {
    members: readonly ProjectMemberResponse[]
    currentUserId: string | null
    isOwnerOrAdmin?: boolean
    availableUsers?: readonly UserListItem[]
    onadd?: (userId: string, role: ProjectMemberRole) => void
    onupdate?: (userId: string, role: ProjectMemberRole) => void
    onremove?: (userId: string) => void
  }

  let {
    members,
    currentUserId,
    isOwnerOrAdmin = false,
    availableUsers = [],
    onadd,
    onupdate,
    onremove,
  }: Props = $props()

  let showAddDialog = $state(false)
  let confirmRemoveUserId = $state<string | null>(null)

  const ROLE_LABELS: Record<ProjectMemberRole, string> = {
    owner: 'Owner',
    annotator: 'Annotator',
    reviewer: 'Reviewer',
  }

  const ROLE_COLORS: Record<ProjectMemberRole, string> = {
    owner: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
    annotator: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    reviewer: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  }

  const ASSIGNABLE_ROLES: ProjectMemberRole[] = ['annotator', 'reviewer']

  function handleRoleChange(userId: string, newRole: string) {
    onupdate?.(userId, newRole as ProjectMemberRole)
  }

  function handleRemoveConfirm() {
    if (confirmRemoveUserId) {
      onremove?.(confirmRemoveUserId)
      confirmRemoveUserId = null
    }
  }

  let nonMemberUsers = $derived(
    availableUsers.filter((u) => !members.some((m) => m.user_id === u.id)),
  )
</script>

<div class="space-y-4">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h3 class="text-foreground text-sm font-semibold">Member Management</h3>
      <p class="text-muted-foreground text-xs">
        Add project members and manage roles.
      </p>
    </div>
    {#if isOwnerOrAdmin}
      <Button variant="outline" size="sm" onclick={() => (showAddDialog = true)}>
        <svg
          class="mr-1 h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        Add Member
      </Button>
    {/if}
  </div>

  <!-- Members Table -->
  {#if members.length > 0}
    <div class="border-border overflow-hidden rounded-lg border">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-muted/50 border-border border-b">
            <th class="text-muted-foreground px-4 py-2 text-left font-medium">Name</th>
            <th class="text-muted-foreground px-4 py-2 text-left font-medium">Email</th>
            <th class="text-muted-foreground px-4 py-2 text-left font-medium">Role</th>
            {#if isOwnerOrAdmin}
              <th class="text-muted-foreground px-4 py-2 text-right font-medium">Action</th>
            {/if}
          </tr>
        </thead>
        <tbody>
          {#each members as member (member.user_id)}
            <tr class="border-border border-b last:border-b-0">
              <td class="text-foreground px-4 py-3 font-medium">
                {member.user_name}
                {#if member.user_id === currentUserId}
                  <span class="text-muted-foreground text-xs">(You)</span>
                {/if}
              </td>
              <td class="text-muted-foreground px-4 py-3">{member.user_email}</td>
              <td class="px-4 py-3">
                {#if isOwnerOrAdmin && member.role !== 'owner'}
                  <select
                    class="border-input bg-background text-foreground focus:border-ring
                      focus:ring-ring rounded-md border px-2 py-1 text-xs focus:ring-1"
                    value={member.role}
                    onchange={(e) => handleRoleChange(member.user_id, e.currentTarget.value)}
                  >
                    {#each ASSIGNABLE_ROLES as role}
                      <option value={role}>{ROLE_LABELS[role]}</option>
                    {/each}
                  </select>
                {:else}
                  <span class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium {ROLE_COLORS[member.role]}">
                    {ROLE_LABELS[member.role]}
                  </span>
                {/if}
              </td>
              {#if isOwnerOrAdmin}
                <td class="px-4 py-3 text-right">
                  {#if member.role !== 'owner' && member.user_id !== currentUserId}
                    <Button
                      variant="ghost"
                      size="sm"
                      class="text-destructive hover:text-destructive h-7 px-2 text-xs"
                      onclick={() => (confirmRemoveUserId = member.user_id)}
                    >
                      Remove
                    </Button>
                  {/if}
                </td>
              {/if}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <div class="border-border rounded-lg border border-dashed p-8 text-center">
      <p class="text-muted-foreground text-sm">No members.</p>
      {#if isOwnerOrAdmin}
        <p class="text-muted-foreground mt-1 text-xs">
          Use the "Add Member" button to add project members.
        </p>
      {/if}
    </div>
  {/if}
</div>

<!-- Remove Confirmation Dialog -->
{#if confirmRemoveUserId}
  {@const memberToRemove = members.find((m) => m.user_id === confirmRemoveUserId)}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    role="dialog"
    aria-modal="true"
    aria-label="Confirm member removal"
  >
    <div class="bg-background mx-4 w-full max-w-sm rounded-lg p-6 shadow-lg">
      <h3 class="text-foreground mb-2 text-lg font-semibold">Remove Member</h3>
      <p class="text-muted-foreground mb-4 text-sm">
        Remove {memberToRemove?.user_name ?? 'this member'} from the project?
      </p>
      <div class="flex justify-end gap-2">
        <Button variant="outline" size="sm" onclick={() => (confirmRemoveUserId = null)}>
          Cancel
        </Button>
        <Button variant="destructive" size="sm" onclick={handleRemoveConfirm}>
          Remove
        </Button>
      </div>
    </div>
  </div>
{/if}

<!-- Add Member Dialog -->
<AddMemberDialog
  bind:open={showAddDialog}
  users={nonMemberUsers}
  {onadd}
/>
