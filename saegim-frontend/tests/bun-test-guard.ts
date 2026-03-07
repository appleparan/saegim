throw new Error(
  '\n\n' +
    '⚠ Do not use "bun test" — it runs Bun\'s built-in test runner,\n' +
    'which cannot compile Svelte 5 runes ($state, $derived).\n\n' +
    'Use "bun run test" instead (runs vitest).\n',
)
