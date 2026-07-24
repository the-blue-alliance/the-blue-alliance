/// <reference types="vite/client" />
import type { QueryClient } from '@tanstack/react-query';
import {
  HeadContent,
  Outlet,
  Scripts,
  createRootRouteWithContext,
  useLocation,
} from '@tanstack/react-router';
import { Suspense, lazy, useEffect } from 'react';
import { Temporal } from 'temporal-polyfill';
import { z } from 'zod';

import { client as colorsClient } from '~/api/colors/client.gen';
import { client as mobileClient } from '~/api/tba/mobile/client.gen';
import {
  getSearchIndexOptions,
  getStatusOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { client } from '~/api/tba/read/client.gen';
import { AuthContextProvider } from '~/components/tba/auth/auth';
import { MatchModal } from '~/components/tba/match/matchModal';
import { Footer } from '~/components/tba/navigation/footer';
import { Navbar } from '~/components/tba/navigation/navbar';
import { TOCRendererProvider } from '~/components/tba/tableOfContents';
import { Toaster } from '~/components/ui/sonner';
import { TooltipProvider } from '~/components/ui/tooltip';
import appleTouchIcon180 from '~/images/apple-splash/apple-touch-icon-180.png?url&no-inline';
import { ApiError } from '~/lib/apiError';
import { APPLE_SPLASH_STARTUP_LINKS } from '~/lib/appleSplashLinks';
import { createCachedFetch } from '~/lib/middleware/network-cache';
import { STALE_TIME } from '~/lib/queryClient';
import { ThemeProvider } from '~/lib/theme';
import { cn, createLogger } from '~/lib/utils';
import appCss from '~/style/tailwind.css?url';

const logger = createLogger('root');

// Devtools are dev-only and must never ship to production. Lazy-loading them
// (instead of a static import) keeps both packages out of the production
// bundle entirely, rather than just tree-shaking an unused render.
const TanStackRouterDevtools = import.meta.env.PROD
  ? null
  : lazy(() =>
      import('@tanstack/react-router-devtools').then((m) => ({
        default: m.TanStackRouterDevtools,
      })),
    );
const ReactQueryDevtools = import.meta.env.PROD
  ? null
  : lazy(() =>
      import('@tanstack/react-query-devtools').then((m) => ({
        default: m.ReactQueryDevtools,
      })),
    );

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

// Attach the HTTP status code to thrown errors so the QueryClient's retry
// function can distinguish 4xx "client error" failures from transient ones.
client.interceptors.error.use((_error, response) => {
  return new ApiError(
    response?.statusText || String(response?.status ?? 0),
    response?.status ?? 0,
  );
});

// Same ApiError mapping for the colors client — consumers rely on 404s being
// skipped and 4xx not being retried (see queryClient.ts).
colorsClient.interceptors.error.use((_error, response) => {
  return new ApiError(
    response?.statusText || String(response?.status ?? 0),
    response?.status ?? 0,
  );
});

// SSR-only network LRU under the API client. Client freshness is owned by
// React Query staleTime — do not install a second TTL in the browser.
if (typeof window === 'undefined') {
  client.setConfig({
    fetch: createCachedFetch({
      cacheableMethods: ['GET'],
    }),
  });
}

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
  // `/status` gates the default year/page-size params for most of the site
  // (see app/lib/queryClient.ts's STALE_TIME.STATUS doc comment), so it's
  // resolved once here rather than independently by every route loader. With
  // STALE_TIME.STATUS this is a cache read after the first navigation.
  beforeLoad: async ({ context: { queryClient } }) => {
    const status = await queryClient.ensureQueryData({
      ...getStatusOptions({}),
      staleTime: STALE_TIME.STATUS,
    });
    // Kick off /search_index on the client without awaiting so navbar search
    // is usually ready by first open, without blocking navigations or
    // dehydrating the large payload into every SSR response (see #10254).
    if (!import.meta.env.SSR) {
      void queryClient.prefetchQuery({
        ...getSearchIndexOptions({}),
        staleTime: STALE_TIME.SEARCH_INDEX,
      });
    }
    return {
      status,
      currentSeason: status.current_season ?? Temporal.Now.plainDateISO().year,
    };
  },
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
      { rel: 'manifest', href: '/manifest.webmanifest' },
      { rel: 'apple-touch-icon', href: appleTouchIcon180 },
      ...APPLE_SPLASH_STARTUP_LINKS,
    ],
  }),
  component: RootComponent,
});

const FULLSCREEN_ROUTES = ['/gameday'];
const FULLWIDTH_ROUTES = ['/match_suggestion'];

function RootComponent() {
  const { pathname } = useLocation();

  // Set data-hydrated on <body> after React mounts so Playwright tests can
  // wait for full client-side hydration before interacting with the page.
  useEffect(() => {
    document.body.setAttribute('data-hydrated', 'true');
  }, []);
  const isFullscreen = FULLSCREEN_ROUTES.some((route) =>
    pathname.startsWith(route),
  );
  const isFullwidth = FULLWIDTH_ROUTES.some((route) =>
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
          <TooltipProvider delay={300} timeout={0}>
            <AuthContextProvider>
              {isFullscreen ? (
                <Outlet />
              ) : (
                <div className="flex min-h-screen flex-col">
                  <Navbar />
                  <TOCRendererProvider>
                    <div
                      className={cn(
                        !isFullwidth && 'container mx-auto',
                        'flex-1 px-4 text-sm',
                      )}
                    >
                      <div vaul-drawer-wrapper="" className="bg-background">
                        <Outlet />
                        <MatchModal />
                      </div>
                    </div>
                  </TOCRendererProvider>
                  <Footer />
                </div>
              )}
            </AuthContextProvider>
          </TooltipProvider>
          <Toaster />
        </ThemeProvider>
        {!import.meta.env.PROD && (
          <Suspense fallback={null}>
            {TanStackRouterDevtools && (
              <TanStackRouterDevtools position="bottom-right" />
            )}
            {ReactQueryDevtools && (
              <ReactQueryDevtools buttonPosition="bottom-left" />
            )}
          </Suspense>
        )}
        <Scripts />
      </body>
    </html>
  );
}
