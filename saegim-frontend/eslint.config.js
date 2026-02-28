import js from '@eslint/js'
import ts from 'typescript-eslint'
import svelte from 'eslint-plugin-svelte'
import prettier from 'eslint-config-prettier'
import globals from 'globals'

export default ts.config(
  // Global ignores
  { ignores: ['build/', '.svelte-kit/', 'dist/', 'node_modules/'] },

  // Base JS recommended rules
  js.configs.recommended,

  // TypeScript recommended rules (non-type-aware)
  ...ts.configs.recommended,

  // Svelte recommended rules
  ...svelte.configs['flat/recommended'],

  // Formatter compat — disables ESLint rules that conflict with oxfmt (via eslint-config-prettier)
  prettier,
  ...svelte.configs['flat/prettier'],

  // Global settings
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
  },

  // Svelte file overrides
  {
    files: ['**/*.svelte', '**/*.svelte.ts', '**/*.svelte.js'],
    languageOptions: {
      parserOptions: {
        parser: ts.parser,
      },
    },
  },

  // Custom rule overrides
  {
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
        },
      ],
      // adapter-static SPA with no base path — resolve() not needed
      'svelte/no-navigation-without-resolve': 'off',
      // Each key is best practice but not critical — warn for gradual adoption
      'svelte/require-each-key': 'warn',
      // PDF.js canvas rendering requires direct DOM manipulation
      'svelte/no-dom-manipulating': 'warn',
      // Konva internal Map is not reactive state
      'svelte/prefer-svelte-reactivity': 'warn',
    },
  },

  // Svelte files: allow unused expressions for $effect dependency tracking
  {
    files: ['**/*.svelte'],
    rules: {
      '@typescript-eslint/no-unused-expressions': 'off',
    },
  },

  // Test file relaxations
  {
    files: ['tests/**/*.ts'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
)
