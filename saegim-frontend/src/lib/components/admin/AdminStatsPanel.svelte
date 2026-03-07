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
      <Card.Description>총 사용자</Card.Description>
      <Card.Title class="text-3xl">{stats.total_users}</Card.Title>
    </Card.Header>
    <Card.Content>
      <p class="text-muted-foreground text-xs">활성 사용자: {stats.active_users}명</p>
    </Card.Content>
  </Card.Root>

  <Card.Root>
    <Card.Header>
      <Card.Description>총 프로젝트</Card.Description>
      <Card.Title class="text-3xl">{stats.total_projects}</Card.Title>
    </Card.Header>
    <Card.Content>
      <p class="text-muted-foreground text-xs">총 페이지: {stats.total_pages}</p>
    </Card.Content>
  </Card.Root>

  <Card.Root>
    <Card.Header>
      <Card.Description>전체 완료율</Card.Description>
      <Card.Title class="text-3xl">{stats.completion_rate}%</Card.Title>
    </Card.Header>
    <Card.Content>
      <p class="text-muted-foreground text-xs">
        완료: {stats.completed_pages} / 검수 대기: {stats.submitted_pages}
      </p>
    </Card.Content>
  </Card.Root>
</div>
