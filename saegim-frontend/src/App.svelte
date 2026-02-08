<script lang="ts">
  import Router, { type RouteDetail } from 'svelte-spa-router'
  import ProjectList from './pages/ProjectList.svelte'
  import DocumentList from './pages/DocumentList.svelte'
  import LabelingPage from './pages/LabelingPage.svelte'

  const routes = new Map<string | RegExp, typeof ProjectList>()
  routes.set('/', ProjectList)
  routes.set('/projects/:id', DocumentList)
  routes.set('/label/:pageId', LabelingPage)

  function conditionsFailed(event: CustomEvent<RouteDetail>) {
    console.error('Route conditions failed:', event.detail)
  }
</script>

<div class="h-full flex flex-col bg-gray-50 text-gray-900">
  <Router {routes} on:conditionsFailed={conditionsFailed} />
</div>
