import { Schema, ValidateEnv } from '@julr/vite-plugin-validate-env';
import { reactRouter } from '@react-router/dev/vite';
import { sentryVitePlugin } from '@sentry/vite-plugin';
import tailwindcss from '@tailwindcss/vite';
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
    reactRouter(),
    tsconfigPaths(),
    tailwindcss(),
    Icons({
      compiler: 'jsx',
      jsx: 'react',
    }),
    sentryVitePlugin({
      org: 'the-blue-alliance',
      project: 'the-blue-alliance-pwa',
    }),
    ValidateEnv({
      VITE_TBA_API_READ_KEY: Schema.string({
        message: 'Get your API key at https://www.thebluealliance.com/account',
      }),
    }),
  ],
  build: {
    sourcemap: true,
  },
  define: {
    __COMMIT_HASH__: JSON.stringify(getCommitHash()),
  },
});
