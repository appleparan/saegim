<script lang="ts">
  import * as Card from '$lib/components/ui/card'
  import type { AdminStatsResponse } from '$lib/api/types'

  interface Props {
    stats: AdminStatsResponse
  }

  let { stats }: Props = $props()
</script>

<div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
  <Card.Root>
    <Card.Header>
      <Card.Description>Total Users</Card.Description>
      <Card.Title class="text-3xl">{stats.total_users}</Card.Title>
    </Card.Header>
    <Card.Content>
      <p class="text-muted-foreground text-xs">Active users: {stats.active_users}</p>
    </Card.Content>
  </Card.Root>

  <Card.Root>
    <Card.Header>
      <Card.Description>Total Projects</Card.Description>
      <Card.Title class="text-3xl">{stats.total_projects}</Card.Title>
    </Card.Header>
    <Card.Content>
      <p class="text-muted-foreground text-xs">Total Pages: {stats.total_pages}</p>
    </Card.Content>
  </Card.Root>

  <Card.Root>
    <Card.Header>
      <Card.Description>Overall Completion</Card.Description>
      <Card.Title class="text-3xl">{stats.completion_rate}%</Card.Title>
    </Card.Header>
    <Card.Content>
      <p class="text-muted-foreground text-xs">
        Complete: {stats.completed_pages} / Review Pending: {stats.submitted_pages}
      </p>
    </Card.Content>
  </Card.Root>
</div>
