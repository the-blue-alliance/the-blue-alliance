import { Schema, ValidateEnv } from '@julr/vite-plugin-validate-env';
import { reactRouter } from '@react-router/dev/vite';
import { sentryVitePlugin } from '@sentry/vite-plugin';
import * as child from 'child_process';
import Icons from 'unplugin-icons/vite';
import { defineConfig } from 'vite';
import tsconfigPaths from 'vite-tsconfig-paths';

// declare module '@react-router/node' {
//   // or cloudflare, deno, etc.
//   interface Future {
//     v3_singleFetch: true;
//   }
// }

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
    Icons({
      compiler: 'jsx',
      jsx: 'react',
    }),
    // TODO: add once https://github.com/vite-pwa/remix/issues/15 is fixed
    // RemixVitePWAPlugin({
    //   strategies: 'generateSW',
    //   manifest: {
    //     name: 'The Blue Alliance',
    //     short_name: 'TBA',
    //     description:
    //       'The Blue Alliance is the best way to scout, watch, and relive the FIRST Robotics Competition.',
    //     start_url: '/?homescreen=1',
    //     display: 'standalone',
    //     theme_color: '#3F51B5',
    //     background_color: '#3F51B5',
    //     icons: [
    //       {
    //         src: 'icons/icon-64.png',
    //         sizes: '64x64',
    //         type: 'image/png',
    //       },
    //       {
    //         src: 'icons/icon-192.png',
    //         sizes: '192x192',
    //         type: 'image/png',
    //       },
    //       {
    //         src: 'icons/icon-512.png',
    //         sizes: '512x512',
    //         type: 'image/png',
    //         purpose: 'any',
    //       },
    //       {
    //         src: 'icons/maskable-icon-512.png',
    //         sizes: '512x512',
    //         type: 'image/png',
    //         purpose: 'maskable',
    //       },
    //     ],
    //   },
    // }),
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
