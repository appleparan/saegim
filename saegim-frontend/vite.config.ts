import { defineConfig } from 'vitest/config'
import { sveltekit } from '@sveltejs/kit/vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss(), sveltekit()],
  test: {
    include: ['tests/**/*.test.ts'],
    environment: 'jsdom',
    setupFiles: ['tests/setup.ts'],
    server: {
      deps: {
        inline: [/svelte/],
      },
    },
    alias: {
      '$app/navigation': 'tests/__mocks__/$app/navigation.ts',
      '$app/state': 'tests/__mocks__/$app/state.ts',
    },
  },
  optimizeDeps: {
    include: ['pdfjs-dist'],
  },
  resolve: {
    conditions: ['browser'],
  },
})
