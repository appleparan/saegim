<script lang="ts">
  import { goto } from '$app/navigation'
  import Header from '$lib/components/layout/Header.svelte'
  import { Button } from '$lib/components/ui/button'
  import * as Tabs from '$lib/components/ui/tabs'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import AdminUsersPanel from '$lib/components/admin/AdminUsersPanel.svelte'
  import AdminProjectsPanel from '$lib/components/admin/AdminProjectsPanel.svelte'
  import AdminStatsPanel from '$lib/components/admin/AdminStatsPanel.svelte'
  import {
    listAdminUsers,
    updateAdminUser,
    listAdminProjects,
    getAdminStats,
  } from '$lib/api/admin'
  import type {
    AdminUserResponse,
    AdminProjectResponse,
    AdminStatsResponse,
    UserRole,
  } from '$lib/api/types'
  import { authStore } from '$lib/stores/auth.svelte'
  import { NetworkError } from '$lib/api/client'

  let users = $state<readonly AdminUserResponse[]>([])
  let projects = $state<readonly AdminProjectResponse[]>([])
  let stats = $state<AdminStatsResponse | null>(null)
  let isLoading = $state(true)
  let error = $state<string | null>(null)
  let successMessage = $state<string | null>(null)

  // Admin route guard
  $effect(() => {
    if (!authStore.isAdmin) {
      goto('/')
    }
  })

  function showSuccess(msg: string) {
    successMessage = msg
    setTimeout(() => (successMessage = null), 3000)
  }

  async function loadData() {
    isLoading = true
    error = null
    try {
      const [userList, projectList, statsData] = await Promise.all([
        listAdminUsers(),
        listAdminProjects(),
        getAdminStats(),
      ])
      users = userList
      projects = projectList
      stats = statsData
    } catch (e) {
      if (e instanceof NetworkError) {
        error = 'Cannot connect to the backend server.'
      } else {
        error = 'Admin Failed to load data.'
      }
    } finally {
      isLoading = false
    }
  }

  async function handleRoleChange(userId: string, role: UserRole) {
    error = null
    try {
      const updated = await updateAdminUser(userId, { role })
      users = users.map((u) => (u.id === userId ? updated : u))
      showSuccess('Role updated.')
    } catch {
      error = 'Failed to update role.'
    }
  }

  async function handleToggleActive(userId: string, isActive: boolean) {
    error = null
    try {
      const updated = await updateAdminUser(userId, { is_active: isActive })
      users = users.map((u) => (u.id === userId ? updated : u))
      showSuccess(isActive ? 'User activated.' : 'User deactivated.')
    } catch {
      error = 'Failed to update user status.'
    }
  }

  $effect(() => {
    if (authStore.isAdmin) {
      loadData()
    }
  })
</script>

<div class="flex h-full flex-col">
  <Header title="Admin Dashboard" />

  <div class="bg-background flex-1 overflow-y-auto p-8">
    <div class="mx-auto max-w-5xl">
      <div class="mb-6">
        <h1 class="text-foreground text-2xl font-bold">Admin Dashboard</h1>
        <p class="text-muted-foreground mt-1 text-sm">Manage the whole system.</p>
      </div>

      {#if isLoading}
        <div class="py-12">
          <LoadingSpinner message="Loading data..." />
        </div>
      {:else if error}
        <div
          class="bg-destructive/10 dark:bg-destructive/20 border-destructive/30
            rounded-xl border p-6 text-center"
        >
          <p class="text-destructive mb-4 font-medium">{error}</p>
          <Button variant="outline" onclick={loadData}>Retry</Button>
        </div>
      {:else}
        {#if successMessage}
          <div
            class="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3
              text-sm text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/30
              dark:text-emerald-300"
          >
            {successMessage}
          </div>
        {/if}

        <Tabs.Root value="users" class="w-full">
          <Tabs.List class="mb-4">
            <Tabs.Trigger value="users">User Admin</Tabs.Trigger>
            <Tabs.Trigger value="projects">Project Admin</Tabs.Trigger>
            <Tabs.Trigger value="stats">System Status</Tabs.Trigger>
          </Tabs.List>

          <Tabs.Content value="users">
            <div class="card-modern p-6">
              <AdminUsersPanel
                {users}
                onrolechange={handleRoleChange}
                ontoggleactive={handleToggleActive}
              />
            </div>
          </Tabs.Content>

          <Tabs.Content value="projects">
            <div class="card-modern p-6">
              <AdminProjectsPanel {projects} />
            </div>
          </Tabs.Content>

          <Tabs.Content value="stats">
            {#if stats}
              <AdminStatsPanel {stats} />
            {/if}
          </Tabs.Content>
        </Tabs.Root>
      {/if}
    </div>
  </div>
</div>
