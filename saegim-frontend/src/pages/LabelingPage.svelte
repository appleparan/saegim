<script lang="ts">
  let { params }: { params: { pageId: string } } = $props()
</script>

<div class="flex-1 p-8">
  <h1 class="text-2xl font-bold mb-4">Labeling</h1>
  <p class="text-gray-500">Page ID: {params?.pageId ?? 'unknown'}</p>
  <p class="text-gray-500">Labeling workspace will be implemented here.</p>
</div>
