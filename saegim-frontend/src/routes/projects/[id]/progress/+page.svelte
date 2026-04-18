<script lang="ts">
  import { page } from '$app/state'
  import Header from '$lib/components/layout/Header.svelte'
  import { Button } from '$lib/components/ui/button'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import { getProject, getProjectProgress } from '$lib/api/projects'
  import type { ProjectResponse, ProjectProgressResponse } from '$lib/api/types'
  import { NetworkError } from '$lib/api/client'
  import { untrack } from 'svelte'

  let project = $state<ProjectResponse | null>(null)
  let progress = $state<ProjectProgressResponse | null>(null)
  let isLoading = $state(true)
  let error = $state<string | null>(null)

  function roleLabel(role: string): string {
    const labels: Record<string, string> = {
      owner: 'Owner',
      annotator: 'Annotator',
      reviewer: 'Reviewer',
    }
    return labels[role] ?? role
  }

  const statusConfig = [
    { key: 'pending' as const, label: 'Pending', color: 'text-muted-foreground', bg: 'bg-muted' },
    {
      key: 'in_progress' as const,
      label: 'In Progress',
      color: 'text-blue-700 dark:text-blue-300',
      bg: 'bg-blue-50 dark:bg-blue-950/30',
      border: 'border-blue-200 dark:border-blue-800',
    },
    {
      key: 'submitted' as const,
      label: 'Submitted',
      color: 'text-amber-700 dark:text-amber-300',
      bg: 'bg-amber-50 dark:bg-amber-950/30',
      border: 'border-amber-200 dark:border-amber-800',
    },
    {
      key: 'reviewed' as const,
      label: 'Reviewed',
      color: 'text-emerald-700 dark:text-emerald-300',
      bg: 'bg-emerald-50 dark:bg-emerald-950/30',
      border: 'border-emerald-200 dark:border-emerald-800',
    },
  ]

  async function loadData() {
    const projectId = page.params.id
    if (!projectId) return
    isLoading = true
    error = null
    try {
      const [proj, prog] = await Promise.all([
        getProject(projectId),
        getProjectProgress(projectId),
      ])
      project = proj
      progress = prog
    } catch (e) {
      if (e instanceof NetworkError) {
        error = 'Cannot connect to the backend server.'
      } else {
        error = 'Failed to load data.'
      }
    } finally {
      isLoading = false
    }
  }

  $effect(() => {
    void page.params.id
    untrack(() => loadData())
  })
</script>

<div class="flex h-full flex-col">
  <Header title={project?.name ?? 'saegim'} />

  <div class="bg-background flex-1 overflow-y-auto p-8">
    <div class="mx-auto max-w-5xl">
      <div class="mb-4">
        <a
          href="/projects/{page.params.id}"
          class="text-muted-foreground hover:text-primary flex w-fit items-center gap-1 text-sm transition-colors"
        >
          <svg
            class="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          {project?.name ?? 'Project'}
        </a>
      </div>

      <div class="mb-6">
        <h1 class="text-foreground text-2xl font-bold">Task Progress</h1>
        <p class="text-muted-foreground mt-1 text-sm">View overall project progress</p>
      </div>

      {#if isLoading}
        <div class="py-12">
          <LoadingSpinner message="Loading progress..." />
        </div>
      {:else if error}
        <div
          class="bg-destructive/10 dark:bg-destructive/20 border-destructive/30 rounded-xl border p-6 text-center"
        >
          <div
            class="bg-destructive/20 mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl"
          >
            <svg
              class="text-destructive h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
              />
            </svg>
          </div>
          <p class="text-destructive mb-4 font-medium">{error}</p>
          <Button variant="outline" onclick={loadData}>Retry</Button>
        </div>
      {:else if progress}
        <!-- Summary Cards -->
        <div class="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div class="card-modern p-5">
            <div class="text-muted-foreground mb-1 text-sm">Total Pages</div>
            <div class="text-foreground text-2xl font-bold">{progress.total_pages}</div>
          </div>
          <div class="card-modern p-5">
            <div class="text-muted-foreground mb-1 text-sm">Completion</div>
            <div class="flex items-center gap-3">
              <div class="text-foreground text-2xl font-bold">{progress.completion_rate}%</div>
              <div class="bg-muted h-2.5 flex-1 overflow-hidden rounded-full">
                <div
                  class="bg-primary h-full rounded-full transition-all"
                  style="width: {progress.completion_rate}%"
                ></div>
              </div>
            </div>
          </div>
          <div class="card-modern p-5">
            <div class="text-muted-foreground mb-1 text-sm">Review Pending</div>
            <div class="text-foreground text-2xl font-bold">
              {progress.status_breakdown.submitted}
            </div>
          </div>
        </div>

        <!-- Status Breakdown -->
        <div class="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {#each statusConfig as cfg (cfg.key)}
            <div class="rounded-xl border {cfg.border ?? 'border-border'} {cfg.bg} p-4">
              <div class="text-muted-foreground text-xs">{cfg.label}</div>
              <div class="mt-1 text-xl font-bold {cfg.color}">
                {progress.status_breakdown[cfg.key]}
              </div>
            </div>
          {/each}
        </div>

        <!-- Documents Table -->
        {#if progress.documents.length > 0}
          <div class="mb-8">
            <h2 class="text-foreground mb-3 text-lg font-semibold">Progress by Document</h2>
            <div class="card-modern overflow-hidden">
              <div class="overflow-x-auto">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-border border-b">
                      <th class="text-muted-foreground px-4 py-3 text-left font-medium">Document</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">Page</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">Pending</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">In Progress</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">Submit</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">Complete</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">Progress</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each progress.documents as doc (doc.document_id)}
                      <tr class="border-border hover:bg-muted/50 border-b last:border-b-0">
                        <td class="text-foreground px-4 py-3 font-medium">{doc.filename}</td>
                        <td class="text-muted-foreground px-3 py-3 text-right">
                          {doc.total_pages}
                        </td>
                        <td class="px-3 py-3 text-right">{doc.status_counts.pending}</td>
                        <td class="px-3 py-3 text-right">{doc.status_counts.in_progress}</td>
                        <td class="px-3 py-3 text-right">{doc.status_counts.submitted}</td>
                        <td class="px-3 py-3 text-right">{doc.status_counts.reviewed}</td>
                        <td class="px-3 py-3 text-right">
                          <div class="flex items-center justify-end gap-2">
                            <div class="bg-muted h-2 w-16 overflow-hidden rounded-full">
                              <div
                                class="bg-primary h-full rounded-full transition-all"
                                style="width: {doc.completion_rate}%"
                              ></div>
                            </div>
                            <span class="text-muted-foreground w-10 text-xs">
                              {doc.completion_rate}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        {/if}

        <!-- Members Table -->
        {#if progress.members.length > 0}
          <div>
            <h2 class="text-foreground mb-3 text-lg font-semibold">Activity by Member</h2>
            <div class="card-modern overflow-hidden">
              <div class="overflow-x-auto">
                <table class="w-full text-sm">
                  <thead>
                    <tr class="border-border border-b">
                      <th class="text-muted-foreground px-4 py-3 text-left font-medium">Name</th>
                      <th class="text-muted-foreground px-3 py-3 text-left font-medium">Role</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">Assigned</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">In Progress</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">Submit</th>
                      <th class="text-muted-foreground px-3 py-3 text-right font-medium">Complete</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each progress.members as member (member.user_id)}
                      <tr class="border-border hover:bg-muted/50 border-b last:border-b-0">
                        <td class="text-foreground px-4 py-3 font-medium">{member.user_name}</td>
                        <td class="px-3 py-3">
                          <span
                            class="bg-muted text-muted-foreground inline-block rounded-md px-2 py-0.5 text-xs"
                          >
                            {roleLabel(member.role)}
                          </span>
                        </td>
                        <td class="px-3 py-3 text-right">{member.assigned_pages}</td>
                        <td class="px-3 py-3 text-right">{member.in_progress_pages}</td>
                        <td class="px-3 py-3 text-right">{member.submitted_pages}</td>
                        <td class="px-3 py-3 text-right">{member.reviewed_pages}</td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        {/if}
      {/if}
    </div>
  </div>
</div>
