import { includeIgnoreFile } from '@eslint/compat';
import tsParser from '@typescript-eslint/parser';
import eslintConfigPrettier from 'eslint-config-prettier/flat';
import importPlugin from 'eslint-plugin-import';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import noRelativeImportPaths from 'eslint-plugin-no-relative-import-paths';
import pluginReact from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import tseslint from 'typescript-eslint';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const gitignorePath = path.resolve(__dirname, '.gitignore');

export default tseslint.config([
  // Ignore files
  includeIgnoreFile(gitignorePath),
  {
    ignores: ['app/api/v3.ts', 'eslint.config.js'],
  },

  // Typescript config
  {
    files: ['**/*.{ts,tsx}'],
    extends: [tseslint.configs.recommendedTypeChecked],
    languageOptions: {
      parserOptions: {
        projectService: {
          allowDefaultProject: ['*.js'],
        },
        tsconfigRootDir: import.meta.dirname,
      },
      parser: tsParser,
    },
    rules: {
      'prefer-promise-reject-errors': ['error'],
      'no-console': 'warn',
      'no-else-return': 'error',
      '@typescript-eslint/only-throw-error': [
        'error',
        {
          allow: ['Response'],
        },
      ],
      '@typescript-eslint/no-non-null-assertion': ['error'],
      '@typescript-eslint/no-throw-literal': 'off',
      '@typescript-eslint/restrict-template-expressions': [
        'error',
        { allowNumber: true },
      ],
    },
  },

  // React
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      pluginReact.configs.flat.recommended,
      pluginReact.configs.flat['jsx-runtime'],
    ],
    settings: { react: { version: 'detect' } },
    languageOptions: { globals: globals.browser },
    rules: {
      'react/prop-types': 'off',
      'react/no-unknown-property': [
        'error',
        { ignore: ['vaul-drawer-wrapper'] },
      ],
    },
  },

  // React Hooks
  {
    files: ['**/*.{ts,tsx}'],
    plugins: {
      'react-hooks': reactHooks,
    },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
  },

  // Node
  {
    files: ['server.js', 'entry.server.tsx'],
    languageOptions: {
      globals: globals.node,
      parser: tsParser,
    },
  },

  // Imports resolve correctly
  {
    files: ['**/*.{ts,tsx,js}'],
    extends: [
      importPlugin.flatConfigs.recommended,
      importPlugin.flatConfigs.react,
      importPlugin.flatConfigs.typescript,
    ],
    settings: {
      'import/resolver': {
        typescript: {
          project: path.resolve(__dirname, 'tsconfig.json'),
        },
        node: {
          paths: ['.', '.react-router/types'],
        },
      },
    },
    rules: {
      'import/no-unresolved': ['error', { ignore: ['^~icons/', '^virtual:'] }],
    },
  },

  // A11y
  {
    files: ['**/*.{ts,tsx}'],
    extends: [jsxA11y.flatConfigs.recommended],
  },

  // No relative import paths
  {
    files: ['**/*.{ts,tsx,js}'],
    plugins: {
      'no-relative-import-paths': noRelativeImportPaths,
    },
    rules: {
      'no-relative-import-paths/no-relative-import-paths': 'error',
    },
  },

  // Prettier
  eslintConfigPrettier,
]);
