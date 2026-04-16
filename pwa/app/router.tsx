import * as Sentry from '@sentry/tanstackstart-react';
import { QueryClient } from '@tanstack/react-query';
import { createRouter } from '@tanstack/react-router';
import { setupRouterSsrQueryIntegration } from '@tanstack/react-router-ssr-query';
import { useEffect } from 'react';

import { ApiError } from '~/lib/apiError';
import registerServiceWorker from '~/lib/serviceWorkerRegistration';
import { createLogger } from '~/lib/utils';
import { routeTree } from '~/routeTree.gen';

const queryCacheLogger = createLogger('queryCache');
const routerLogger = createLogger('router');

export function getRouter() {
  // Don't retry 4xx responses — they indicate a client or data error (e.g. 404
  // "not found") that won't resolve on retry. Retrying them causes unnecessary
  // background re-renders for the full exponential-backoff window (~10s).
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: (failureCount, error) => {
          if (
            error instanceof ApiError &&
            error.status >= 400 &&
            error.status < 500
          ) {
            return false;
          }
          return failureCount < 3;
        },
      },
    },
  });
  queryClient.getQueryCache().subscribe((event) => {
    // Only log "added" events (new queries) and "updated" events when query completes successfully
    // This reduces noise from intermediate state transitions (loading states)
    if (event.type === 'added') {
      queryCacheLogger.info(
        {
          type: event.type,
          // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
          queryKey: event.query.queryKey[0]._id,
          // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
          path: event.query.queryKey[0].path,
        },
        'Query cache event',
      );
    } else if (
      event.type === 'updated' &&
      event.query.state.status === 'success' &&
      event.query.state.data !== undefined
    ) {
      // Only log successful updates with data (not loading states)
      queryCacheLogger.info(
        {
          type: event.type,
          // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
          queryKey: event.query.queryKey[0]._id,
          // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
          path: event.query.queryKey[0].path,
        },
        'Query cache event',
      );
    }
  });

  const router = createRouter({
    routeTree,
    context: {
      queryClient,
    },
    scrollRestoration: ({ location }) => {
      return location.pathname !== '/apidocs/v3';
    },
    // Scalar updates window.location.hash as you scroll through API docs; without
    // this, TanStack Router's hashScrollIntoView causes the page to snap/jump.
    // TableOfContents uses e.preventDefault() so it's unaffected by this setting.
    defaultHashScrollIntoView: false,
    caseSensitive: true,
    defaultErrorComponent: ErrorComponent,
    defaultNotFoundComponent: NotFoundComponent,
  });
  setupRouterSsrQueryIntegration({
    router,
    queryClient,
  });

  if (!router.isServer) {
    Sentry.init({
      dsn: 'https://1420d805bff3f6f12a13817725266abd@o4507688293695488.ingest.us.sentry.io/4507745278492672',
      sendDefaultPii: false,
      enableLogs: true,
      enableMetrics: true,
      tracesSampleRate: 1,
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1,
      profilesSampleRate: 1,

      integrations: [Sentry.tanstackRouterBrowserTracingIntegration(router)],
      enabled: process.env.NODE_ENV === 'production',
    });
    void registerServiceWorker();
  }

  return router;
}

function ErrorComponent({ error }: { error: Error }) {
  routerLogger.error(error, 'Router error');

  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <div className="py-8">
      <h1 className="mb-3 text-3xl font-medium">Oh Noes!1!!</h1>
      <h2 className="text-2xl">An error occurred.</h2>
    </div>
  );
}

function NotFoundComponent() {
  return (
    <div className="py-8">
      <h1 className="mb-3 text-3xl font-medium">Oh Noes!1!!</h1>
      <h2 className="text-2xl">Error 404 - Page Not Found</h2>
    </div>
  );
}
