import queryPlugin from '@tanstack/eslint-plugin-query';
import routerPlugin from '@tanstack/eslint-plugin-router';
import { defineConfig } from 'oxlint';

const ALL_TS_FILES = ['**/*.{ts,tsx}'];
const ALL_TS_JS_FILES = ['**/*.{ts,tsx,js}'];

// Each plugin's `correctness` rules are on by default, so this config only
// lists deviations from that baseline: rules in other categories that we want
// enforced, severity changes, and rule options.
export default defineConfig({
  plugins: [
    'eslint',
    'import',
    'jsx-a11y',
    'node',
    'oxc',
    'promise',
    'react-perf',
    'react',
    'typescript',
    'unicorn',
    'vitest',
  ],
  options: {
    typeAware: true,
  },
  ignorePatterns: [
    '**/node_modules',
    '.cache',
    'build',
    'coverage',
    '**/.env',
    'test-results/',
    'playwright-report/',
    'blob-report/',
    'playwright/.cache/',
    '**/.react-router/',
    '**/.tanstack/',
    'server.js',
    '**/.playwright-mcp/',
    'app/api/tba/',
    'app/api/colors/',
    'pnpm-lock.yaml',
  ],
  rules: {},
  overrides: [
    {
      files: ALL_TS_FILES,
      env: { browser: true },
      rules: {},
    },
    {
      files: ['server.js', 'entry.server.tsx'],
      env: { node: true },
    },
    {
      files: ALL_TS_JS_FILES,
      jsPlugins: ['eslint-plugin-no-relative-import-paths'],
      rules: {
        'no-relative-import-paths/no-relative-import-paths': 'error',
      },
    },
    {
      files: ALL_TS_FILES,
      jsPlugins: ['oxlint-tailwindcss'],
      rules: {
        // Correctness — catch real bugs
        'tailwindcss/no-conflicting-classes': 'error',
        'tailwindcss/no-deprecated-classes': 'error',
        'tailwindcss/no-duplicate-classes': 'warn',
        'tailwindcss/no-unknown-classes': [
          'error',
          {
            // Marker class that Sonner's `group-[.toaster]:` selectors target;
            // it is not meant to produce CSS of its own.
            allowlist: ['toaster'],
            // The plugin registers the `group`/`peer` markers but not their
            // user-defined `/name` suffixes, so `group/foo` reads as unknown.
            ignorePrefixes: ['group/', 'peer/'],
          },
        ],

        // Modernization — keep classes in current canonical form
        'tailwindcss/enforce-canonical': 'warn',
        'tailwindcss/no-unnecessary-arbitrary-value': 'warn',

        // Style and consistency
        'tailwindcss/enforce-sort-order': 'warn',
        'tailwindcss/consistent-variant-order': 'warn',
        'tailwindcss/enforce-consistent-important-position': 'warn',
        'tailwindcss/no-unnecessary-whitespace': 'warn',
      },
    },
    {
      files: ALL_TS_JS_FILES,
      jsPlugins: ['@tanstack/eslint-plugin-query'],
      rules: {
        ...queryPlugin.configs.recommended.rules,
        // Query keys are scoped by `user?.uid`; the Firebase User object itself
        // is not key-safe (its toJSON embeds the rotating stsTokenManager), so
        // `user` in a queryFn is not a missing queryKey dependency.
        '@tanstack/query/exhaustive-deps': [
          'error',
          { allowlist: { variables: ['user'] } },
        ],
      },
    },
    {
      files: ALL_TS_JS_FILES,
      jsPlugins: ['@tanstack/eslint-plugin-router'],
      rules: {
        ...routerPlugin.configs.recommended.rules,
      },
    },
  ],
  settings: {
    tailwindcss: {
      entryPoint: 'app/style/tailwind.css',
    },
  },
});
