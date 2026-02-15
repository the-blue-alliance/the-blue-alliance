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
import { useEffect } from 'react';
import { Temporal } from 'temporal-polyfill';
import { z } from 'zod';

import { client as mobileClient } from '~/api/tba/mobile/client.gen';
import { client } from '~/api/tba/read/client.gen';
import { AuthContextProvider } from '~/components/tba/auth/auth';
import { MatchModal } from '~/components/tba/match/matchModal';
import { Footer } from '~/components/tba/navigation/footer';
import { Navbar } from '~/components/tba/navigation/navbar';
import { TOCRendererProvider } from '~/components/tba/tableOfContents';
import { Toaster } from '~/components/ui/sonner';
import appleTouchIcon180 from '~/images/apple-splash/apple-touch-icon-180.png?url&no-inline';
import { ApiError } from '~/lib/apiError';
import { APPLE_SPLASH_STARTUP_LINKS } from '~/lib/appleSplashLinks';
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

// Attach the HTTP status code to thrown errors so the QueryClient's retry
// function can distinguish 4xx "client error" failures from transient ones.
client.interceptors.error.use((_error, response) => {
  return new ApiError(
    response.statusText || String(response.status),
    response.status,
  );
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
  loader: () => ({
    renderTime: Temporal.Now.zonedDateTimeISO().toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      hour12: true,
    }),
  }),
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
      ...APPLE_SPLASH_STARTUP_LINKS,
    ],
  }),
  component: RootComponent,
});

const FULLSCREEN_ROUTES = ['/gameday'];

function RootComponent() {
  const { renderTime } = Route.useLoaderData();
  const { pathname } = useLocation();

  // Set data-hydrated on <body> after React mounts so Playwright tests can
  // wait for full client-side hydration before interacting with the page.
  useEffect(() => {
    document.body.setAttribute('data-hydrated', 'true');
  }, []);
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
                <Footer renderTime={renderTime} />
              </>
            )}
          </AuthContextProvider>
          <Toaster />
        </ThemeProvider>
        <TanStackRouterDevtools position="bottom-right" />
        <ReactQueryDevtools buttonPosition="bottom-left" />
        <Scripts />
      </body>
    </html>
  );
}
