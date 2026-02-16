/// <reference types="vite/client" />
import type { QueryClient } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import {
  HeadContent,
  Outlet,
  Scripts,
  createRootRouteWithContext,
  useLocation,
} from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools';
import { z } from 'zod';

import { client as mobileClient } from '~/api/tba/mobile/client.gen';
import { client } from '~/api/tba/read/client.gen';
import { AuthContextProvider } from '~/components/tba/auth/auth';
import { MatchModal } from '~/components/tba/match/matchModal';
import { Footer } from '~/components/tba/navigation/footer';
import { Navbar } from '~/components/tba/navigation/navbar';
import { TOCRendererProvider } from '~/components/tba/tableOfContents';
import splashLandscape1136x640 from '~/images/apple-splash/apple-splash-landscape-1136x640.png?url&no-inline';
import splashLandscape1334x750 from '~/images/apple-splash/apple-splash-landscape-1334x750.png?url&no-inline';
import splashLandscape1792x828 from '~/images/apple-splash/apple-splash-landscape-1792x828.png?url&no-inline';
import splashLandscape2048x1536 from '~/images/apple-splash/apple-splash-landscape-2048x1536.png?url&no-inline';
import splashLandscape2160x1620 from '~/images/apple-splash/apple-splash-landscape-2160x1620.png?url&no-inline';
import splashLandscape2208x1242 from '~/images/apple-splash/apple-splash-landscape-2208x1242.png?url&no-inline';
import splashLandscape2224x1668 from '~/images/apple-splash/apple-splash-landscape-2224x1668.png?url&no-inline';
import splashLandscape2388x1668 from '~/images/apple-splash/apple-splash-landscape-2388x1668.png?url&no-inline';
import splashLandscape2436x1125 from '~/images/apple-splash/apple-splash-landscape-2436x1125.png?url&no-inline';
import splashLandscape2532x1170 from '~/images/apple-splash/apple-splash-landscape-2532x1170.png?url&no-inline';
import splashLandscape2556x1179 from '~/images/apple-splash/apple-splash-landscape-2556x1179.png?url&no-inline';
import splashLandscape2688x1242 from '~/images/apple-splash/apple-splash-landscape-2688x1242.png?url&no-inline';
import splashLandscape2732x2048 from '~/images/apple-splash/apple-splash-landscape-2732x2048.png?url&no-inline';
import splashLandscape2778x1284 from '~/images/apple-splash/apple-splash-landscape-2778x1284.png?url&no-inline';
import splashLandscape2796x1290 from '~/images/apple-splash/apple-splash-landscape-2796x1290.png?url&no-inline';
import splashPortrait640x1136 from '~/images/apple-splash/apple-splash-portrait-640x1136.png?url&no-inline';
import splashPortrait750x1334 from '~/images/apple-splash/apple-splash-portrait-750x1334.png?url&no-inline';
import splashPortrait828x1792 from '~/images/apple-splash/apple-splash-portrait-828x1792.png?url&no-inline';
import splashPortrait1125x2436 from '~/images/apple-splash/apple-splash-portrait-1125x2436.png?url&no-inline';
import splashPortrait1170x2532 from '~/images/apple-splash/apple-splash-portrait-1170x2532.png?url&no-inline';
import splashPortrait1179x2556 from '~/images/apple-splash/apple-splash-portrait-1179x2556.png?url&no-inline';
import splashPortrait1242x2208 from '~/images/apple-splash/apple-splash-portrait-1242x2208.png?url&no-inline';
import splashPortrait1242x2688 from '~/images/apple-splash/apple-splash-portrait-1242x2688.png?url&no-inline';
import splashPortrait1284x2778 from '~/images/apple-splash/apple-splash-portrait-1284x2778.png?url&no-inline';
import splashPortrait1290x2796 from '~/images/apple-splash/apple-splash-portrait-1290x2796.png?url&no-inline';
import splashPortrait1536x2048 from '~/images/apple-splash/apple-splash-portrait-1536x2048.png?url&no-inline';
import splashPortrait1620x2160 from '~/images/apple-splash/apple-splash-portrait-1620x2160.png?url&no-inline';
import splashPortrait1668x2224 from '~/images/apple-splash/apple-splash-portrait-1668x2224.png?url&no-inline';
import splashPortrait1668x2388 from '~/images/apple-splash/apple-splash-portrait-1668x2388.png?url&no-inline';
import splashPortrait2048x2732 from '~/images/apple-splash/apple-splash-portrait-2048x2732.png?url&no-inline';
import appleTouchIcon180 from '~/images/apple-splash/apple-touch-icon-180.png?url&no-inline';
import { createCachedFetch } from '~/lib/middleware/network-cache';
import { ThemeProvider } from '~/lib/theme';
import { createLogger } from '~/lib/utils';
import appCss from '~/tailwind.css?url';

const logger = createLogger('root');

// Configure request interceptor for auth
client.interceptors.request.use((request) => {
  request.headers.set('X-TBA-Auth-Key', import.meta.env.VITE_TBA_API_READ_KEY);

  logger.info(
    {
      method: request.method,
      url: request.url,
    },
    'Sending request to TBA API',
  );

  return request;
});

// Configure network cache middleware
// Caches API responses in memory across sessions to reduce external API calls
// Cache is a global singleton with 500 max entries and 3 hour TTL
client.setConfig({
  fetch: createCachedFetch({
    cacheableMethods: ['GET'],
  }),
});

// Point mobile API client at local backend when configured
if (import.meta.env.VITE_TBA_MOBILE_API_BASE_URL) {
  mobileClient.setConfig({
    baseUrl: import.meta.env.VITE_TBA_MOBILE_API_BASE_URL,
  });
}

// Search params schema for global modal state
const rootSearchSchema = z.object({
  matchKey: z.string().optional(),
});

export type RootSearchParams = z.infer<typeof rootSearchSchema>;

export const Route = createRootRouteWithContext<{
  queryClient: QueryClient;
}>()({
  validateSearch: rootSearchSchema,
  head: ({ matches }) => ({
    meta: [
      {
        charSet: 'utf-8',
      },
      {
        name: 'color-scheme',
        content: 'light dark',
      },
      {
        name: 'robots',
        content: 'noindex',
      },
      {
        name: 'viewport',
        content: 'width=device-width, initial-scale=1',
      },
      {
        name: 'mobile-web-app-capable',
        content: 'yes',
      },
      {
        title: 'The Blue Alliance',
      },
    ],
    links: [
      {
        rel: 'canonical',
        href: `https://www.thebluealliance.com${matches[matches.length - 1].pathname}`,
      },
      {
        rel: 'stylesheet',
        href: appCss,
      },
      { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
      {
        rel: 'preconnect',
        href: 'https://fonts.gstatic.com',
        crossOrigin: 'anonymous',
      },
      {
        rel: 'stylesheet',
        href: 'https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap',
      },
      { rel: 'manifest', href: '/manifest.webmanifest' },
      { rel: 'apple-touch-icon', href: appleTouchIcon180 },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)',
        href: splashPortrait2048x2732,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)',
        href: splashLandscape2732x2048,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 834px) and (device-height: 1194px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)',
        href: splashPortrait1668x2388,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 834px) and (device-height: 1194px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)',
        href: splashLandscape2388x1668,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)',
        href: splashPortrait1536x2048,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)',
        href: splashLandscape2048x1536,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 834px) and (device-height: 1112px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)',
        href: splashPortrait1668x2224,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 834px) and (device-height: 1112px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)',
        href: splashLandscape2224x1668,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 810px) and (device-height: 1080px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)',
        href: splashPortrait1620x2160,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 810px) and (device-height: 1080px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)',
        href: splashLandscape2160x1620,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 430px) and (device-height: 932px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)',
        href: splashPortrait1290x2796,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 430px) and (device-height: 932px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)',
        href: splashLandscape2796x1290,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)',
        href: splashPortrait1179x2556,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)',
        href: splashLandscape2556x1179,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 428px) and (device-height: 926px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)',
        href: splashPortrait1284x2778,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 428px) and (device-height: 926px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)',
        href: splashLandscape2778x1284,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)',
        href: splashPortrait1170x2532,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)',
        href: splashLandscape2532x1170,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)',
        href: splashPortrait1125x2436,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)',
        href: splashLandscape2436x1125,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)',
        href: splashPortrait1242x2688,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)',
        href: splashLandscape2688x1242,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)',
        href: splashPortrait828x1792,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)',
        href: splashLandscape1792x828,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 414px) and (device-height: 736px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)',
        href: splashPortrait1242x2208,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 414px) and (device-height: 736px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)',
        href: splashLandscape2208x1242,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)',
        href: splashPortrait750x1334,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)',
        href: splashLandscape1334x750,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)',
        href: splashPortrait640x1136,
      },
      {
        rel: 'apple-touch-startup-image',
        media:
          'screen and (device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)',
        href: splashLandscape1136x640,
      },
    ],
  }),
  component: RootComponent,
});

const FULLSCREEN_ROUTES = ['/gameday'];

function RootComponent() {
  const { pathname } = useLocation();
  const isFullscreen = FULLSCREEN_ROUTES.some((route) =>
    pathname.startsWith(route),
  );

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          // This render-blocking script is necessary to ensure the correct theme is applied when the page is loaded.
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('theme');
                  var isDark = theme === 'dark' || 
                    (theme !== 'light' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                  if (isDark) {
                    document.documentElement.classList.add('dark');
                  }
                } catch (e) {}
              })();
            `,
          }}
        />
        <HeadContent />
      </head>
      <body>
        <ThemeProvider>
          <AuthContextProvider>
            {isFullscreen ? (
              <Outlet />
            ) : (
              <>
                <Navbar />
                <TOCRendererProvider>
                  <div
                    className="container mx-auto
                      min-h-[calc(100vh-var(--header-height)-var(--footer-min-height)-var(--footer-inset-top))]
                      px-4 text-sm"
                  >
                    <div vaul-drawer-wrapper="" className="bg-background">
                      <Outlet />
                      <MatchModal />
                    </div>
                  </div>
                </TOCRendererProvider>
                <Footer />
              </>
            )}
          </AuthContextProvider>
        </ThemeProvider>
        <TanStackRouterDevtools position="bottom-right" />
        <ReactQueryDevtools buttonPosition="bottom-left" />
        <Scripts />
      </body>
    </html>
  );
}
