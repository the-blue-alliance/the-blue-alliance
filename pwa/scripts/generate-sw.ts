import { generateSW } from 'workbox-build';

async function buildServiceWorker() {
  try {
    console.log('🔧 Generating service worker with Workbox...');

    const result = await generateSW({
      // Directory to scan for files to precache
      globDirectory: 'build/client',

      // Patterns to match files for precaching
      globPatterns: ['**/*.{js,css,png,jpg,jpeg,svg,woff,woff2,ico}'],

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
