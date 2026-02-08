<script lang="ts">
  import Header from '$lib/components/layout/Header.svelte'
  import Sidebar from '$lib/components/layout/Sidebar.svelte'
  import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte'
  import Button from '$lib/components/common/Button.svelte'
  import ImageViewer from '$lib/components/canvas/ImageViewer.svelte'
  import ElementList from '$lib/components/panels/ElementList.svelte'
  import AttributePanel from '$lib/components/panels/AttributePanel.svelte'
  import PageAttributePanel from '$lib/components/panels/PageAttributePanel.svelte'
  import TextEditor from '$lib/components/panels/TextEditor.svelte'
  import { annotationStore } from '$lib/stores/annotation.svelte'
  import { canvasStore } from '$lib/stores/canvas.svelte'
  import { uiStore } from '$lib/stores/ui.svelte'
  import { getPage, savePage } from '$lib/api/pages'
  import { NetworkError } from '$lib/api/client'
  import type { PageResponse } from '$lib/api/types'

  let { params }: { params: { pageId: string } } = $props()

  let pageData = $state<PageResponse | null>(null)
  let saving = $state(false)

  async function loadPage() {
    if (!params?.pageId) return
    annotationStore.setLoading(true)
    annotationStore.setError(null)
    try {
      const data = await getPage(params.pageId)
      pageData = data
      annotationStore.load(params.pageId, data.annotation_data)
      canvasStore.setImageDimensions(data.width, data.height)
    } catch (e) {
      if (e instanceof NetworkError) {
        annotationStore.setError('백엔드 서버에 연결할 수 없습니다.')
      } else {
        annotationStore.setError('페이지를 불러오는 데 실패했습니다.')
      }
    } finally {
      annotationStore.setLoading(false)
    }
  }

  async function handleSave() {
    if (!params?.pageId || !annotationStore.annotationData) return
    saving = true
    try {
      await savePage(params.pageId, {
        annotation_data: annotationStore.annotationData,
      })
      annotationStore.markSaved()
      uiStore.showNotification('저장 완료', 'success')
    } catch {
      uiStore.showNotification('저장 실패', 'error')
    } finally {
      saving = false
    }
  }

  $effect(() => {
    loadPage()
  })
</script>

<div class="h-full flex flex-col">
  <Header title="레이블링" showSave onsave={handleSave} {saving} />

  {#if annotationStore.isLoading}
    <div class="flex-1 flex items-center justify-center">
      <LoadingSpinner message="페이지 불러오는 중..." />
    </div>
  {:else if annotationStore.error}
    <div class="flex-1 flex items-center justify-center">
      <div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center max-w-md">
        <p class="text-red-700 mb-4">{annotationStore.error}</p>
        <Button variant="secondary" onclick={loadPage}>다시 시도</Button>
      </div>
    </div>
  {:else}
    <div class="flex-1 flex overflow-hidden">
      <!-- Left panel: Element list -->
      <div class="w-64 border-r border-gray-200 bg-white overflow-y-auto flex flex-col">
        <ElementList />
      </div>

      <!-- Center: Canvas area -->
      <div class="flex-1 relative bg-gray-100">
        <div class="absolute top-3 left-3 z-10 flex gap-1 bg-white rounded-lg shadow-sm border border-gray-200 p-1">
          <Button size="sm" variant="ghost" active={canvasStore.toolMode === 'select'} onclick={() => canvasStore.setTool('select')}>선택</Button>
          <Button size="sm" variant="ghost" active={canvasStore.toolMode === 'draw'} onclick={() => canvasStore.setTool('draw')}>그리기</Button>
          <Button size="sm" variant="ghost" active={canvasStore.toolMode === 'pan'} onclick={() => canvasStore.setTool('pan')}>이동</Button>
          <div class="w-px bg-gray-200 mx-1"></div>
          <Button size="sm" variant="ghost" onclick={() => canvasStore.zoomIn()}>+</Button>
          <Button size="sm" variant="ghost" onclick={() => canvasStore.zoomOut()}>-</Button>
          <Button size="sm" variant="ghost" onclick={() => canvasStore.resetView()}>1:1</Button>
        </div>

        {#if pageData}
          <ImageViewer
            imageUrl={pageData.image_url}
            width={pageData.width}
            height={pageData.height}
          />
        {:else}
          <div class="absolute inset-0 flex items-center justify-center">
            <p class="text-gray-400 text-sm">이미지를 불러오는 중...</p>
          </div>
        {/if}
      </div>

      <!-- Right panel: Sidebar -->
      <Sidebar>
        {#if uiStore.activePanel === 'elements'}
          <AttributePanel />
        {:else if uiStore.activePanel === 'attributes'}
          <PageAttributePanel />
        {:else if uiStore.activePanel === 'text'}
          <TextEditor />
        {/if}
      </Sidebar>
    </div>
  {/if}
</div>
