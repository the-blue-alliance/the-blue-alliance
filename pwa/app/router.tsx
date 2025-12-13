import * as Sentry from '@sentry/tanstackstart-react';
import { QueryClient } from '@tanstack/react-query';
import { createRouter } from '@tanstack/react-router';
import { setupRouterSsrQueryIntegration } from '@tanstack/react-router-ssr-query';
import { routeTree } from 'app/routeTree.gen';
import { useEffect } from 'react';

import { createLogger } from '~/lib/utils';

const queryCacheLogger = createLogger('queryCache');
const routerLogger = createLogger('router');

export function getRouter() {
  const queryClient = new QueryClient();
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

      integrations: [
        // eslint-disable-next-line import/namespace
        Sentry.tanstackRouterBrowserTracingIntegration(router),
      ],
      enabled: process.env.NODE_ENV === 'production',
    });
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
