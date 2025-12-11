import { Schema, ValidateEnv } from '@julr/vite-plugin-validate-env';
import { sentryVitePlugin } from '@sentry/vite-plugin';
import tailwindcss from '@tailwindcss/vite';
import { tanstackStart } from '@tanstack/react-start/plugin/vite';
import viteReact from '@vitejs/plugin-react';
import * as child from 'child_process';
import Icons from 'unplugin-icons/vite';
import { defineConfig } from 'vite';
import tsconfigPaths from 'vite-tsconfig-paths';

function getCommitHash(): string {
  try {
    return child.execSync('git rev-parse --short HEAD').toString();
  } catch {
    return 'unknown';
  }
}

export default defineConfig({
  plugins: [
    tsconfigPaths(),
    tanstackStart({
      srcDirectory: 'app',
    }),
    viteReact({
      babel: {
        plugins: ['babel-plugin-react-compiler'],
      },
    }),
    tailwindcss(),
    Icons({
      compiler: 'jsx',
      jsx: 'react',
    }),
    sentryVitePlugin({
      org: 'the-blue-alliance',
      project: 'the-blue-alliance-pwa',
      authToken: process.env.SENTRY_AUTH_TOKEN,
      sourcemaps: {
        assets: ['./build/client/**/*'],
        ignore: ['**/node_modules/**'],
      },
    }),
    ValidateEnv({
      VITE_TBA_API_READ_KEY: Schema.string({
        message: 'Get your API key at https://www.thebluealliance.com/account',
      }),
    }),
  ],
  build: {
    outDir: 'build',
    sourcemap: true,
  },
  environments: {
    client: {
      build: {
        rollupOptions: {
          output: {
            manualChunks: (id) => {
              if (!id.includes('node_modules')) {
                return undefined;
              }
              if (id.includes('/react/') || id.includes('/react-dom/')) {
                return 'react';
              }
              if (id.includes('@firebase')) {
                return 'firebase';
              }
              if (id.includes('@sentry')) {
                return 'sentry';
              }
              if (id.includes('@tanstack')) {
                return 'tanstack';
              }
              if (id.includes('@radix-ui')) {
                return 'radix-ui';
              }
              if (id.includes('recharts')) {
                return 'recharts';
              }
              if (id.includes('lodash')) {
                return 'lodash';
              }
              if (id.includes('zod')) {
                return 'zod';
              }
              return 'vendor';
            },
          },
        },
      },
    },
  },
  define: {
    __COMMIT_HASH__: JSON.stringify(getCommitHash()),
  },
});
