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
    'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed'

  const variantClasses = {
    primary:
      'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary:
      'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-blue-500',
    danger:
      'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    ghost:
      'text-gray-600 hover:bg-gray-100 hover:text-gray-900 focus:ring-blue-500',
  }

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  }

  const activeClass = active ? 'ring-2 ring-blue-500' : ''
</script>

<button
  class="{baseClasses} {variantClasses[variant]} {sizeClasses[size]} {activeClass}"
  {disabled}
  {onclick}
>
  {@render children()}
</button>
