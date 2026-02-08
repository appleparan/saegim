<script lang="ts">
  import type { RouteDetail } from 'svelte-spa-router'

  let { params }: { params: { id: string } } = $props()
</script>

<div class="flex-1 p-8">
  <h1 class="text-2xl font-bold mb-4">Documents</h1>
  <p class="text-gray-500">Project ID: {params?.id ?? 'unknown'}</p>
  <p class="text-gray-500">Document list will be implemented here.</p>
</div>
