<script lang="ts">
  import type { AdminProjectResponse } from '$lib/api/types'

  interface Props {
    projects: readonly AdminProjectResponse[]
  }

  let { projects }: Props = $props()

  function progressPercent(project: AdminProjectResponse): number {
    if (project.total_pages === 0) return 0
    return Math.round((project.completed_pages / project.total_pages) * 100)
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('ko-KR')
  }
</script>

<div class="space-y-4">
  <div>
    <h3 class="text-foreground text-sm font-semibold">프로젝트 관리</h3>
    <p class="text-muted-foreground text-xs">전체 프로젝트 현황을 확인하세요.</p>
  </div>

  {#if projects.length > 0}
    <div class="border-border overflow-hidden rounded-lg border">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-muted/50 border-border border-b">
            <th class="text-muted-foreground px-4 py-2 text-left font-medium">프로젝트</th>
            <th class="text-muted-foreground px-4 py-2 text-center font-medium">멤버</th>
            <th class="text-muted-foreground px-4 py-2 text-center font-medium">총 페이지</th>
            <th class="text-muted-foreground px-4 py-2 text-center font-medium">완료</th>
            <th class="text-muted-foreground px-4 py-2 text-center font-medium">검수 대기</th>
            <th class="text-muted-foreground px-4 py-2 text-left font-medium">진행률</th>
            <th class="text-muted-foreground px-4 py-2 text-left font-medium">생성일</th>
          </tr>
        </thead>
        <tbody>
          {#each projects as project (project.id)}
            {@const pct = progressPercent(project)}
            <tr class="border-border border-b last:border-b-0">
              <td class="px-4 py-3">
                <div class="text-foreground font-medium">{project.name}</div>
                {#if project.description}
                  <div class="text-muted-foreground text-xs">{project.description}</div>
                {/if}
              </td>
              <td class="text-foreground px-4 py-3 text-center">{project.member_count}</td>
              <td class="text-foreground px-4 py-3 text-center">{project.total_pages}</td>
              <td class="text-foreground px-4 py-3 text-center">{project.completed_pages}</td>
              <td class="text-foreground px-4 py-3 text-center">{project.submitted_pages}</td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <div class="bg-muted h-2 w-20 overflow-hidden rounded-full">
                    <div
                      class="bg-primary h-full rounded-full transition-all"
                      style="width: {pct}%"
                    ></div>
                  </div>
                  <span class="text-muted-foreground text-xs">{pct}%</span>
                </div>
              </td>
              <td class="text-muted-foreground px-4 py-3">{formatDate(project.created_at)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <div class="border-border rounded-lg border border-dashed p-8 text-center">
      <p class="text-muted-foreground text-sm">등록된 프로젝트가 없습니다.</p>
    </div>
  {/if}
</div>
