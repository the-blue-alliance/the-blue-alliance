import { Schema, ValidateEnv } from '@julr/vite-plugin-validate-env';
import { sentryVitePlugin } from '@sentry/vite-plugin';
import tailwindcss from '@tailwindcss/vite';
import { tanstackStart } from '@tanstack/react-start/plugin/vite';
import react from '@vitejs/plugin-react';
import * as child from 'child_process';
import Icons from 'unplugin-icons/vite';
import { defineConfig } from 'vite';

function getCommitHash(): string {
  try {
    return child.execSync('git rev-parse --short HEAD').toString().trim();
  } catch {
    return 'unknown';
  }
}

const staticRoutes = [
  '/about',
  '/add-data',
  '/apidocs',
  '/apidocs/v3',
  '/contact',
  '/donate',
  '/gameday',
  '/privacy',
  '/thanks',
];

export default defineConfig({
  resolve: {
    tsconfigPaths: true,
  },
  plugins: [
    tanstackStart({
      srcDirectory: 'app',
      prerender: {
        enabled: true,
        filter: ({ path }) => staticRoutes.includes(path),
      },
    }),
    react({ compiler: true }),
    tailwindcss(),
    Icons({
      compiler: 'jsx',
      jsx: 'react',
    }),
    sentryVitePlugin({
      org: 'the-blue-alliance',
      project: 'the-blue-alliance-pwa',
      authToken: process.env.SENTRY_AUTH_TOKEN,
      telemetry: process.env.NODE_ENV !== 'test',
      sourcemaps: {
        assets: ['./build/client/**/*'],
        ignore: ['**/node_modules/**'],
      },
    }),
    ValidateEnv({
      VITE_TBA_API_READ_KEY: Schema.string({
        message: 'Get your API key at https://www.thebluealliance.com/account',
      }),
      VITE_FIREBASE_API_KEY: Schema.string({
        message: 'Copy your Firebase config from .env.example',
      }),
      VITE_FIREBASE_AUTH_DOMAIN: Schema.string({
        message: 'Copy your Firebase config from .env.example',
      }),
      VITE_FIREBASE_PROJECT_ID: Schema.string({
        message: 'Copy your Firebase config from .env.example',
      }),
      VITE_FIREBASE_DATABASE_URL: Schema.string({
        message: 'Copy your Firebase config from .env.example',
      }),
      VITE_FIREBASE_APP_ID: Schema.string({
        message: 'Copy your Firebase config from .env.example',
      }),
      VITE_FIREBASE_MEASUREMENT_ID: Schema.string({
        message: 'Copy your Firebase config from .env.example',
      }),
    }),
  ],
  build: {
    outDir: 'build',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('/node_modules/')) return;

          if (id.includes('/temporal-polyfill/')) return 'temporal-polyfill';

          // React core — already eager on every page, one stable long-cache chunk
          if (
            id.includes('/react-dom/') ||
            id.includes('/react/') ||
            id.includes('/scheduler/')
          )
            return 'vendor-react';

          // TanStack router/query/store — eager, spread across ~10 chunks today
          if (id.includes('/@tanstack/')) return 'vendor-tanstack';

          // Base UI primitives + their floating-ui dep — spread across 36 chunks
          if (id.includes('/@base-ui/react/') || id.includes('/@floating-ui/'))
            return 'vendor-baseui';
        },
      },
    },
  },
  define: {
    __COMMIT_HASH__: JSON.stringify(getCommitHash()),
  },
});
