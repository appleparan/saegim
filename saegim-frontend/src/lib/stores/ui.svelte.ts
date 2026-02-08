/**
 * UI state management using Svelte 5 runes.
 */

export type PanelTab = 'elements' | 'attributes' | 'text'
export type NotificationType = 'info' | 'error' | 'success'

export interface Notification {
  readonly message: string
  readonly type: NotificationType
}

class UiStore {
  sidebarOpen = $state(true)
  activePanel = $state<PanelTab>('elements')
  notification = $state<Notification | null>(null)

  private notificationTimer: ReturnType<typeof setTimeout> | null = null

  toggleSidebar(): void {
    this.sidebarOpen = !this.sidebarOpen
  }

  setActivePanel(panel: PanelTab): void {
    this.activePanel = panel
  }

  showNotification(message: string, type: NotificationType = 'info'): void {
    if (this.notificationTimer !== null) {
      clearTimeout(this.notificationTimer)
    }

    this.notification = { message, type }
    this.notificationTimer = setTimeout(() => {
      this.notification = null
      this.notificationTimer = null
    }, 3000)
  }

  dismissNotification(): void {
    if (this.notificationTimer !== null) {
      clearTimeout(this.notificationTimer)
      this.notificationTimer = null
    }
    this.notification = null
  }
}

export const uiStore = new UiStore()
