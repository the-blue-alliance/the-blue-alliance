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

const staticRoutes = [
  '/about',
  '/add-data',
  '/apidocs',
  '/contact',
  '/donate',
  '/gameday',
  '/legal/privacy',
  '/thanks',
];

export default defineConfig({
  plugins: [
    tsconfigPaths(),
    tanstackStart({
      srcDirectory: 'app',
      prerender: {
        enabled: true,
        filter: ({ path }) => staticRoutes.includes(path),
      },
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
  define: {
    __COMMIT_HASH__: JSON.stringify(getCommitHash()),
  },
});
