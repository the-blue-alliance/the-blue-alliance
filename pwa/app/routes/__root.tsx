/// <reference types="vite/client" />
import type { QueryClient } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import {
  HeadContent,
  Outlet,
  Scripts,
  createRootRouteWithContext,
} from '@tanstack/react-router';
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools';
import splashLandscape1136x640 from 'app/images/apple-splash/apple-splash-landscape-1136x640.png?url';
import splashLandscape1334x750 from 'app/images/apple-splash/apple-splash-landscape-1334x750.png?url';
import splashLandscape1792x828 from 'app/images/apple-splash/apple-splash-landscape-1792x828.png?url';
import splashLandscape2048x1536 from 'app/images/apple-splash/apple-splash-landscape-2048x1536.png?url';
import splashLandscape2160x1620 from 'app/images/apple-splash/apple-splash-landscape-2160x1620.png?url';
import splashLandscape2208x1242 from 'app/images/apple-splash/apple-splash-landscape-2208x1242.png?url';
import splashLandscape2224x1668 from 'app/images/apple-splash/apple-splash-landscape-2224x1668.png?url';
import splashLandscape2388x1668 from 'app/images/apple-splash/apple-splash-landscape-2388x1668.png?url';
import splashLandscape2436x1125 from 'app/images/apple-splash/apple-splash-landscape-2436x1125.png?url';
import splashLandscape2532x1170 from 'app/images/apple-splash/apple-splash-landscape-2532x1170.png?url';
import splashLandscape2556x1179 from 'app/images/apple-splash/apple-splash-landscape-2556x1179.png?url';
import splashLandscape2688x1242 from 'app/images/apple-splash/apple-splash-landscape-2688x1242.png?url';
import splashLandscape2732x2048 from 'app/images/apple-splash/apple-splash-landscape-2732x2048.png?url';
import splashLandscape2778x1284 from 'app/images/apple-splash/apple-splash-landscape-2778x1284.png?url';
import splashLandscape2796x1290 from 'app/images/apple-splash/apple-splash-landscape-2796x1290.png?url';
import splashPortrait640x1136 from 'app/images/apple-splash/apple-splash-portrait-640x1136.png?url';
import splashPortrait750x1334 from 'app/images/apple-splash/apple-splash-portrait-750x1334.png?url';
import splashPortrait828x1792 from 'app/images/apple-splash/apple-splash-portrait-828x1792.png?url';
import splashPortrait1125x2436 from 'app/images/apple-splash/apple-splash-portrait-1125x2436.png?url';
import splashPortrait1170x2532 from 'app/images/apple-splash/apple-splash-portrait-1170x2532.png?url';
import splashPortrait1179x2556 from 'app/images/apple-splash/apple-splash-portrait-1179x2556.png?url';
import splashPortrait1242x2208 from 'app/images/apple-splash/apple-splash-portrait-1242x2208.png?url';
import splashPortrait1242x2688 from 'app/images/apple-splash/apple-splash-portrait-1242x2688.png?url';
import splashPortrait1284x2778 from 'app/images/apple-splash/apple-splash-portrait-1284x2778.png?url';
import splashPortrait1290x2796 from 'app/images/apple-splash/apple-splash-portrait-1290x2796.png?url';
import splashPortrait1536x2048 from 'app/images/apple-splash/apple-splash-portrait-1536x2048.png?url';
import splashPortrait1620x2160 from 'app/images/apple-splash/apple-splash-portrait-1620x2160.png?url';
import splashPortrait1668x2224 from 'app/images/apple-splash/apple-splash-portrait-1668x2224.png?url';
import splashPortrait1668x2388 from 'app/images/apple-splash/apple-splash-portrait-1668x2388.png?url';
import splashPortrait2048x2732 from 'app/images/apple-splash/apple-splash-portrait-2048x2732.png?url';
import appleTouchIcon180 from 'app/images/apple-splash/apple-touch-icon-180.png?url';
import appCss from 'app/tailwind.css?url';

import { client } from '~/api/tba/read/client.gen';
import { Nav } from '~/components/tba/nav';
import { createCachedFetch } from '~/lib/middleware/network-cache';

// Configure request interceptor for auth
client.interceptors.request.use((request) => {
  request.headers.set('X-TBA-Auth-Key', import.meta.env.VITE_TBA_API_READ_KEY);
  return request;
});

// Configure network cache middleware
// Caches API responses in memory across sessions to reduce external API calls
client.setConfig({
  fetch: createCachedFetch({
    maxEntries: 500,
    ttl: 10800000, // 3 hours
    debug: false, // Set to true to enable debug logging
    cacheableMethods: ['GET'],
  }),
});

export const Route = createRootRouteWithContext<{
  queryClient: QueryClient;
}>()({
  head: ({ matches }) => ({
    meta: [
      {
        charSet: 'utf-8',
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

function RootComponent() {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        <Nav />
        <div className="container mx-auto px-4 pt-14 text-sm">
          <div vaul-drawer-wrapper="" className="bg-background">
            <Outlet />
          </div>
        </div>
        <TanStackRouterDevtools position="bottom-right" />
        <ReactQueryDevtools buttonPosition="bottom-left" />
        <Scripts />
      </body>
    </html>
  );
}
