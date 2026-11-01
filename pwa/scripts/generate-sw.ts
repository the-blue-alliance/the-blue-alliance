import { generateSW } from 'workbox-build';

import { FULLSCREEN_ROUTES, FULLWIDTH_ROUTES } from '~/lib/layoutRoutes';

async function buildServiceWorker() {
  try {
    console.log('🔧 Generating service worker with Workbox...');

    const result = await generateSW({
      // Directory to scan for files to precache
      globDirectory: 'build/client',

      // Patterns to match files for precaching
      globPatterns: [
        '**/*.{js,css,png,jpg,jpeg,svg,woff,woff2,ico}',
        '_shell.html',
      ],

      // Answer repeat visits with the app shell (see `spa` in
      // vite.config.ts) so page loads never reach the server; the router
      // then loads the page and its data in the browser.
      navigateFallback: '/_shell.html',
      navigateFallbackDenylist: [
        // The shell has the default root layout, which these routes change.
        ...[...FULLSCREEN_ROUTES, ...FULLWIDTH_ROUTES].map(
          (prefix) => new RegExp(`^${prefix}`),
        ),
        // Files opened directly, such as /robots.txt.
        /^[^?]*\.[^/?]*(\?|$)/,
      ],

      // Output location for the generated service worker
      swDest: 'build/client/sw.js',

      // Service worker will take control immediately
      skipWaiting: true,
      clientsClaim: true,

      // Clean up outdated caches
      cleanupOutdatedCaches: true,

      // Cache name configuration
      cacheId: 'tba-pwa',

      // Ignore specific files
      globIgnores: [
        '**/sw.js',
        '**/workbox-*.js',
        '**/*.map',
        '**/apple-splash-*',
      ],

      // Maximum file size to precache (2MB)
      maximumFileSizeToCacheInBytes: 2 * 1024 * 1024,

      // Source map for debugging
      sourcemap: false,
    });

    console.log(`✅ Service worker generated successfully!`);
    console.log(
      `📦 Precached ${result.count} files (${(result.size / 1024 / 1024).toFixed(2)} MB)`,
    );

    if (result.warnings.length > 0) {
      console.warn('⚠️ Warnings:');
      result.warnings.forEach((warning) => console.warn(`   - ${warning}`));
    }
  } catch (error) {
    console.error('❌ Error generating service worker:', error);
    process.exit(1);
  }
}

await buildServiceWorker();
