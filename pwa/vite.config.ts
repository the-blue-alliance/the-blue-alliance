import { vitePlugin as remix } from '@remix-run/dev';
import { RemixVitePWA } from '@vite-pwa/remix';
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

const { RemixVitePWAPlugin, RemixPWAPreset } = RemixVitePWA();

export default defineConfig({
  plugins: [
    remix({
      future: {
        v3_fetcherPersist: true,
        v3_relativeSplatPath: true,
        v3_throwAbortReason: true,
      },
      presets: [RemixPWAPreset()],
    }),
    tsconfigPaths(),
    Icons({
      compiler: 'jsx',
      jsx: 'react',
    }),
    RemixVitePWAPlugin({
      strategies: 'generateSW',
      manifest: {
        name: 'The Blue Alliance',
        short_name: 'TBA',
        description:
          'The Blue Alliance is the best way to scout, watch, and relive the FIRST Robotics Competition.',
        start_url: '/',
        display: 'standalone',
        theme_color: '#3F51B5',
        background_color: '#3F51B5',
        icons: [
          {
            src: 'icons/icon-64.png',
            sizes: '64x64',
            type: 'image/png',
          },
          {
            src: 'icons/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'icons/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: 'icons/maskable-icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
    }),
  ],
  build: {
    sourcemap: true,
  },
  define: {
    __COMMIT_HASH__: JSON.stringify(getCommitHash()),
  },
});
