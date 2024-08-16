/**
 * This is intended to be a basic starting point for linting in your app.
 * It relies on recommended configs out of the box for simplicity, but you can
 * and should modify this configuration to best suit your team's needs.
 */

/** @type {import('eslint').Linter.Config} */
module.exports = {
  root: true,
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  env: {
    browser: true,
    commonjs: true,
    es6: true,
  },
  ignorePatterns: ['!**/.server', '!**/.client', 'app/api/v3.ts'],

  // Base config
  extends: ['eslint:recommended', 'prettier', 'plugin:tailwindcss/recommended'],
  plugins: ['no-relative-import-paths'],
  rules: {
    // Fix for eslint not knowing how to resolve unplugin icons
    'import/no-unresolved': ['error', { ignore: ['^~icons/'] }],
    'tailwindcss/no-custom-classname': 'off',
    'no-relative-import-paths/no-relative-import-paths': [
      'error',
      { allowSameFolder: true },
    ],
    'no-console': 'warn',
    'no-else-return': 'error',
  },

  overrides: [
    // React
    {
      files: ['**/*.{js,jsx,ts,tsx}'],
      plugins: ['react', 'jsx-a11y'],
      parser: '@typescript-eslint/parser',
      extends: [
        'plugin:react/recommended',
        'plugin:react/jsx-runtime',
        'plugin:react-hooks/recommended',
        'plugin:jsx-a11y/recommended',
      ],
      settings: {
        react: {
          version: 'detect',
        },
        formComponents: ['Form'],
        linkComponents: [
          { name: 'Link', linkAttribute: 'to' },
          { name: 'NavLink', linkAttribute: 'to' },
        ],
        'import/resolver': {
          typescript: {},
        },
      },
      rules: {
        // https://github.com/redpangilinan/credenza
        // needs vaul-drawer-wrapper around root element
        'react/no-unknown-property': [
          'error',
          { ignore: ['vaul-drawer-wrapper'] },
        ],
      },
    },

    // Typescript
    {
      files: ['**/*.{ts,tsx}'],
      plugins: ['@typescript-eslint', 'import'],
      parser: '@typescript-eslint/parser',
      settings: {
        'import/internal-regex': '^~/',
        'import/resolver': {
          node: {
            extensions: ['.ts', '.tsx'],
          },
          typescript: {
            alwaysTryTypes: true,
          },
        },
      },
      extends: [
        'plugin:@typescript-eslint/strict-type-checked',
        'plugin:@typescript-eslint/stylistic-type-checked',
        'plugin:import/recommended',
        'plugin:import/typescript',
      ],
      parserOptions: {
        project: ['tsconfig.json'],
      },
      rules: {
        // See https://github.com/typescript-eslint/typescript-eslint/issues/6226
        '@typescript-eslint/no-throw-literal': 'off',
        '@typescript-eslint/restrict-template-expressions': [
          'error',
          { allowNumber: true },
        ],
        // See https://github.com/typescript-eslint/typescript-eslint/issues/6226
        '@typescript-eslint/only-throw-error': [
          'off',
          { allowThrowingAny: false, allowThrowingUnknown: false },
        ],
      },
    },

    // Node
    {
      files: ['.eslintrc.cjs'],
      env: {
        node: true,
      },
    },

    // Fix for stock shadcn components
    // https://github.com/shadcn-ui/ui/issues/120
    {
      files: ['app/components/ui/*.tsx'],
      rules: {
        'react/prop-types': ['off'],
      },
    },
  ],
};
