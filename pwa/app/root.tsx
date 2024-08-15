import {
  isRouteErrorResponse,
  Links,
  Meta,
  MetaFunction,
  Outlet,
  Scripts,
  ScrollRestoration,
  useRouteError,
} from '@remix-run/react';
import * as Sentry from '@sentry/react';
import './tailwind.css';
import * as api from '~/api/v3';
import { LRUCache } from 'lru-cache';

Sentry.init({
  dsn: 'https://1420d805bff3f6f12a13817725266abd@o4507688293695488.ingest.us.sentry.io/4507745278492672',
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
  ],
  // Performance Monitoring
  tracesSampleRate: 1.0, //  Capture 100% of the transactions
  // Set 'tracePropagationTargets' to control for which URLs distributed tracing should be enabled
  tracePropagationTargets: [/^https:\/\/beta\.thebluealliance\.com/],
  // Session Replay
  replaysSessionSampleRate: 0.1, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
  replaysOnErrorSampleRate: 1.0, // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
  enabled: process.env.NODE_ENV === 'production',
});

api.defaults.baseUrl = 'https://www.thebluealliance.com/api/v3/';
api.defaults.headers = {
  'X-TBA-Auth-Key': import.meta.env.VITE_TBA_API_READ_KEY,
};

// Custom fetch that uses an in-memory cache to handle ETags.
// TODO: Maybe also use localStorage for clients?
const cache = new LRUCache<string, Response>({
  max: 500,
});
api.defaults.fetch = async (url, options = {}) => {
  if (options.method && options.method !== 'GET') {
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
        <Links />
      </head>
      <body>
        <div className="container mx-auto text-sm">
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

export default function App() {
  return <Outlet />;
}

export const meta: MetaFunction = ({ error }) => {
  const isRouteError = isRouteErrorResponse(error);
  const title =
    isRouteError && error.status === 404 ? '404 - Page Not Found' : 'Error';
  return [{ title: error ? title : 'The Blue Alliance' }];
};

export function ErrorBoundary() {
  const error = useRouteError();
  const isRouteError = isRouteErrorResponse(error);
  return (
    <>
      <h1 className="mb-2.5 mt-5 text-4xl">Oh Noes!1!!</h1>
      <h2 className="text-2xl">
        {isRouteError ? `Error ${error.status}` : 'An unknown error occurred.'}
      </h2>
    </>
  );
}
