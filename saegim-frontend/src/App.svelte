<script lang="ts">
  import Router, { type RouteDefinition } from 'svelte-spa-router'
  import ProjectList from './pages/ProjectList.svelte'
  import DocumentList from './pages/DocumentList.svelte'
  import ProjectSettings from './pages/ProjectSettings.svelte'
  import LabelingPage from './pages/LabelingPage.svelte'

  // svelte-spa-router v4 types expect Svelte 4 class components;
  // Svelte 5 function components are runtime-compatible but need a type cast
  const routes = {
    '/': ProjectList,
    '/projects/:id': DocumentList,
    '/projects/:id/settings': ProjectSettings,
    '/label/:pageId': LabelingPage,
  } as unknown as RouteDefinition
</script>

<div class="h-full flex flex-col bg-gray-50 text-gray-900">
  <Router {routes} />
</div>
