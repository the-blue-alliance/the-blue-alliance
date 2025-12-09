import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Sentry from '@sentry/react';
import { createAsyncStoragePersister } from '@tanstack/query-async-storage-persister';
import { QueryClient, isServer } from '@tanstack/react-query';
import { persistQueryClient } from '@tanstack/react-query-persist-client';
import { createRouter } from '@tanstack/react-router';
import { setupRouterSsrQueryIntegration } from '@tanstack/react-router-ssr-query';
import { routeTree } from 'app/routeTree.gen';

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 1000 * 60 * 5,
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined = undefined;

function getQueryClient() {
  if (isServer) {
    return makeQueryClient();
  } else {
    if (!browserQueryClient) {
      browserQueryClient = makeQueryClient();
      const localStoragePersister = createAsyncStoragePersister({
        storage: AsyncStorage,
      });
      persistQueryClient({
        queryClient: browserQueryClient,
        persister: localStoragePersister,
      });
    }
    return browserQueryClient;
  }
}

export function getRouter() {
  const queryClient = getQueryClient();
  const router = createRouter({
    routeTree,
    context: {
      queryClient,
    },
    scrollRestoration: true,
    defaultErrorComponent: ErrorComponent,
    defaultNotFoundComponent: NotFoundComponent,
  });
  setupRouterSsrQueryIntegration({
    router,
    queryClient,
  });

  Sentry.init({
    dsn: 'https://1420d805bff3f6f12a13817725266abd@o4507688293695488.ingest.us.sentry.io/4507745278492672',
    tracesSampleRate: 1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1,
    profilesSampleRate: 1,

    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
      Sentry.browserProfilingIntegration(),
    ],
    enabled: process.env.NODE_ENV === 'production',
  });

  return router;
}

function ErrorComponent({ error }: { error: Error }) {
  console.error(error);
  Sentry.captureException(error);

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
