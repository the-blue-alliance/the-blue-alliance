import { Schema, ValidateEnv } from '@julr/vite-plugin-validate-env';
import babel from '@rolldown/plugin-babel';
import { sentryVitePlugin } from '@sentry/vite-plugin';
import tailwindcss from '@tailwindcss/vite';
import { tanstackStart } from '@tanstack/react-start/plugin/vite';
import react, { reactCompilerPreset } from '@vitejs/plugin-react';
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
    react(),
    babel({
      presets: [reactCompilerPreset()],
      include: [/\.(ts|tsx|js|jsx)$/],
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
