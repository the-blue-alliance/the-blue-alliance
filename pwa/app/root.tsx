import {
  Links,
  Meta,
  MetaFunction,
  Outlet,
  Scripts,
  ScrollRestoration,
  isRouteErrorResponse,
  useRouteError,
} from '@remix-run/react';
import { captureRemixErrorBoundaryError, withSentry } from '@sentry/remix';
import { LRUCache } from 'lru-cache';
import { pwaInfo } from 'virtual:pwa-info';

import * as api from '~/api/v3';

import GlobalLoadingProgress from './components/tba/globalLoadingProgress';
import { Nav } from './components/tba/nav';
import './tailwind.css';

api.defaults.baseUrl = 'https://www.thebluealliance.com/api/v3/';
api.defaults.headers = {
  'X-TBA-Auth-Key': import.meta.env.VITE_TBA_API_READ_KEY,
};

// Custom fetch that uses an in-memory cache to handle ETags.
// TODO: Maybe also use localStorage for clients?
// TODO: Fix CORS on client
const isServer = typeof window === 'undefined';
const cache = new LRUCache<string, Response>({
  max: 500,
});
api.defaults.fetch = async (url, options = {}) => {
  if ((options.method && options.method !== 'GET') || !isServer) {
    return fetch(url, options);
  }

  // Only cache GET requests
  const cachedResponse = cache.get(url as string);
  const etag = cachedResponse?.headers.get('ETag');
  if (cachedResponse && etag) {
    (options.headers as Headers).set('If-None-Match', etag);
  }

  const response = await fetch(url, options);
  if (response.status === 304 && cachedResponse) {
    return cachedResponse.clone();
  }

  if (response.status === 200 && response.headers.has('ETag')) {
    cache.set(url as string, response.clone());
  }
  return response;
};

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap"
          rel="stylesheet"
        />
        <Meta />
        {pwaInfo ? (
          <link rel="manifest" href={pwaInfo.webManifest.href} />
        ) : null}
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <link rel="apple-touch-icon" href="/icons/apple-touch-icon-180.png" />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-2048x2732.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-2732x2048.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 834px) and (device-height: 1194px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-1668x2388.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 834px) and (device-height: 1194px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-2388x1668.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-1536x2048.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-2048x1536.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 834px) and (device-height: 1112px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-1668x2224.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 834px) and (device-height: 1112px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-2224x1668.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 810px) and (device-height: 1080px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-1620x2160.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 810px) and (device-height: 1080px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-2160x1620.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 430px) and (device-height: 932px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-1290x2796.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 430px) and (device-height: 932px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-2796x1290.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-1179x2556.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-2556x1179.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 428px) and (device-height: 926px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-1284x2778.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 428px) and (device-height: 926px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-2778x1284.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-1170x2532.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-2532x1170.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-1125x2436.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-2436x1125.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-1242x2688.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-2688x1242.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-828x1792.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 414px) and (device-height: 896px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-1792x828.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 414px) and (device-height: 736px) and (-webkit-device-pixel-ratio: 3) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-1242x2208.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 414px) and (device-height: 736px) and (-webkit-device-pixel-ratio: 3) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-2208x1242.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-750x1334.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-1334x750.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2) and (orientation: portrait)"
          href="/icons/apple-splash-portrait-640x1136.png"
        />
        <link
          rel="apple-touch-startup-image"
          media="screen and (device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2) and (orientation: landscape)"
          href="/icons/apple-splash-landscape-1136x640.png"
        />
        <Links />
      </head>
      <body>
        <GlobalLoadingProgress />
        <Nav />
        <div className="container mx-auto text-sm px-4 pt-14">
          <div vaul-drawer-wrapper="" className="bg-background">
            {children}
          </div>
        </div>
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

function App() {
  return <Outlet />;
}

export default withSentry(App);

export const meta: MetaFunction = ({ error }) => {
  const isRouteError = isRouteErrorResponse(error);
  const title =
    isRouteError && error.status === 404 ? '404 - Page Not Found' : 'Error';
  return [{ title: error ? title : 'The Blue Alliance' }];
};

export function ErrorBoundary() {
  const error = useRouteError();
  const isRouteError = isRouteErrorResponse(error);
  captureRemixErrorBoundaryError(error);
  return (
    <>
      <h1 className="mb-2.5 mt-5 text-4xl">Oh Noes!1!!</h1>
      <h2 className="text-2xl">
        {isRouteError ? `Error ${error.status}` : 'An unknown error occurred.'}
      </h2>
    </>
  );
}
