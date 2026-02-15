<script lang="ts">
  import type { Snippet } from 'svelte'

  interface Props {
    variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
    size?: 'sm' | 'md' | 'lg'
    disabled?: boolean
    active?: boolean
    onclick?: (e: MouseEvent) => void
    children: Snippet
  }

  let {
    variant = 'secondary',
    size = 'md',
    disabled = false,
    active = false,
    onclick,
    children,
  }: Props = $props()

  const baseClasses =
    'inline-flex items-center justify-center font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed'

  const variantClasses = {
    primary:
      'bg-primary-600 text-white hover:bg-primary-500 active:bg-primary-700 focus:ring-primary-500 shadow-sm',
    secondary:
      'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 hover:border-gray-300 focus:ring-primary-500 shadow-sm',
    danger:
      'bg-red-600 text-white hover:bg-red-500 active:bg-red-700 focus:ring-red-500 shadow-sm',
    ghost:
      'text-gray-600 hover:bg-gray-100 hover:text-gray-900 focus:ring-primary-500',
  }

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  }

  const activeClass = $derived(active ? 'ring-2 ring-primary-500' : '')
</script>

<button
  class="{baseClasses} {variantClasses[variant]} {sizeClasses[size]} {activeClass}"
  {disabled}
  {onclick}
>
  {@render children()}
</button>
