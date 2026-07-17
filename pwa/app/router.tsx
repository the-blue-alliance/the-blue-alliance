import * as Sentry from '@sentry/tanstackstart-react';
import { ParsedLocation, createRouter } from '@tanstack/react-router';
import { setupRouterSsrQueryIntegration } from '@tanstack/react-router-ssr-query';
import { useEffect } from 'react';
import { toast } from 'sonner';

import ClipboardCopyIcon from '~icons/lucide/clipboard-copy';

import { Button } from '~/components/ui/button';
import { createQueryClient } from '~/lib/queryClient';
import registerServiceWorker from '~/lib/serviceWorkerRegistration';
import { createLogger } from '~/lib/utils';
import { routeTree } from '~/routeTree.gen';

const queryCacheLogger = createLogger('queryCache');
const routerLogger = createLogger('router');

export function getRouter() {
  const queryClient = createQueryClient();
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

    router.subscribe(
      'onResolved',
      ({ toLocation }: { toLocation: ParsedLocation }) => {
        void logPageView(toLocation.pathname, toLocation.href);
      },
    );

    // onResolved doesn't fire for the initial hydration, so log it manually.
    void logPageView(window.location.pathname, window.location.href);
  }

  return router;
}

// Firebase is dynamically imported here (mirroring the pattern in
// useFirebaseWebcasts.ts) so `firebase/analytics` and firebaseConfig.tsx
// (which also pulls in firebase/app and firebase/auth) stay out of the
// entry chunk and only load once a client-side navigation actually happens.
async function logPageView(pagePath: string, pageLocation: string) {
  const [{ logEvent }, { analytics }] = await Promise.all([
    import('firebase/analytics'),
    import('~/firebase/firebaseConfig'),
  ]);

  if (analytics === null) {
    return;
  }

  logEvent(analytics, 'page_view', {
    page_path: pagePath,
    page_location: pageLocation,
    client_platform: 'pwa', // GA4 custom dimension
  });
}

function ErrorComponent({ error }: { error: Error }) {
  routerLogger.error(error, 'Router error');

  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  const stack = error.stack ?? error.message;

  const agentPrompt = [
    'I ran into the following error. Please find the root cause. ',
    '',
    `URL: ${window.location.href}`,
    '',
    'Stack trace:',
    '```',
    stack,
    '```',
  ].join('\n');

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`Copied ${label} to clipboard!`);
    } catch {
      toast.error('Failed to copy to clipboard.');
    }
  };

  return (
    <div className="py-8">
      <h1 className="mb-3 text-3xl font-medium">Oh Noes!1!!</h1>
      <h2 className="text-2xl">An error occurred.</h2>
      {process.env.NODE_ENV !== 'production' && error.stack && (
        <>
          <div className="mt-4 flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => void copyToClipboard(stack, 'stack trace')}
            >
              <ClipboardCopyIcon />
              Copy stack trace
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => void copyToClipboard(agentPrompt, 'agent prompt')}
            >
              <ClipboardCopyIcon />
              Copy with agent prompt
            </Button>
          </div>
          <pre
            className="mt-4 overflow-x-auto rounded bg-muted p-4 text-sm
              whitespace-pre-wrap"
          >
            {error.stack}
          </pre>
        </>
      )}
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
