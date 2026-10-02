import type { QueryClient } from '@tanstack/react-query';
import type { ErrorComponentProps } from '@tanstack/react-router';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ComponentType } from 'react';
import { type Mock, beforeEach, describe, expect, test, vi } from 'vitest';

import { ApiError } from '~/lib/apiError';

interface RouterOptions {
  context: { queryClient: QueryClient };
  scrollRestoration: (args: { location: { pathname: string } }) => boolean;
  defaultErrorComponent: ComponentType<ErrorComponentProps>;
  defaultNotFoundComponent: ComponentType;
  routeTree: unknown;
}

type ResolvedListener = (event: {
  toLocation: { pathname: string; href: string };
}) => void;

const mocks = vi.hoisted(() => ({
  state: { isServer: false },
  createRouter: vi.fn<(options: unknown) => unknown>(),
  subscribe: vi.fn<(event: string, listener: unknown) => void>(),
  setupRouterSsrQueryIntegration: vi.fn<(options: unknown) => void>(),
  sentryInit: vi.fn<(options: unknown) => void>(),
  captureException: vi.fn<(error: unknown) => void>(),
  tracingIntegration: vi.fn<(router: unknown) => unknown>(),
  registerServiceWorker: vi.fn<() => Promise<void>>(),
  logEvent:
    vi.fn<(analytics: unknown, name: string, params: unknown) => void>(),
  getAnalyticsInstance: vi.fn<() => Promise<unknown>>(),
  toastSuccess: vi.fn<(message: string) => void>(),
  toastError: vi.fn<(message: string) => void>(),
  loggers: new Map<
    string,
    {
      debug: Mock<(data: unknown, message: string) => void>;
      error: Mock<(data: unknown, message: string) => void>;
    }
  >(),
}));

vi.mock('@tanstack/react-router', () => ({
  createRouter: mocks.createRouter,
}));

vi.mock('@tanstack/react-router-ssr-query', () => ({
  setupRouterSsrQueryIntegration: mocks.setupRouterSsrQueryIntegration,
}));

vi.mock('@sentry/tanstackstart-react', () => ({
  init: mocks.sentryInit,
  captureException: mocks.captureException,
  tanstackRouterBrowserTracingIntegration: mocks.tracingIntegration,
}));

vi.mock('~/routeTree.gen', () => ({ routeTree: { id: 'root' } }));

vi.mock('~/lib/serviceWorkerRegistration', () => ({
  default: mocks.registerServiceWorker,
}));

vi.mock('firebase/analytics', () => ({ logEvent: mocks.logEvent }));

vi.mock('~/firebase/firebaseConfig', () => ({
  getAnalyticsInstance: mocks.getAnalyticsInstance,
}));

vi.mock('sonner', () => ({
  toast: { success: mocks.toastSuccess, error: mocks.toastError },
}));

vi.mock('~/lib/logger', () => ({
  createLogger: (name: string) => {
    const logger = {
      debug: vi.fn<(data: unknown, message: string) => void>(),
      error: vi.fn<(data: unknown, message: string) => void>(),
    };
    mocks.loggers.set(name, logger);
    return logger;
  },
}));

const { getRouter } = await import('~/router');

function logger(name: string) {
  const found = mocks.loggers.get(name);
  if (!found) throw new Error(`No logger named ${name}`);
  return found;
}

function createAndCapture() {
  const router = getRouter() as { isServer: boolean };
  const options = mocks.createRouter.mock.calls[0][0] as RouterOptions;
  return { router, options };
}

describe('getRouter', () => {
  beforeEach(() => {
    mocks.state.isServer = false;
    mocks.createRouter.mockImplementation(() => ({
      get isServer() {
        return mocks.state.isServer;
      },
      subscribe: mocks.subscribe,
    }));
    mocks.registerServiceWorker.mockResolvedValue();
    mocks.getAnalyticsInstance.mockResolvedValue({ name: 'analytics' });
    mocks.tracingIntegration.mockReturnValue({ name: 'tracing' });
    logger('queryCache').debug.mockReset();
    logger('router').error.mockReset();
  });

  test('builds the router with the query client and route tree', () => {
    const { router, options } = createAndCapture();

    expect(options.routeTree).toEqual({ id: 'root' });
    expect(mocks.setupRouterSsrQueryIntegration).toHaveBeenCalledWith({
      router,
      queryClient: options.context.queryClient,
    });
    expect(options).toMatchObject({
      defaultPreload: 'intent',
      defaultPreloadStaleTime: 0,
      defaultHashScrollIntoView: false,
      caseSensitive: true,
    });
  });

  test('restores scroll everywhere except the API docs', () => {
    const { options } = createAndCapture();

    expect(options.scrollRestoration({ location: { pathname: '/' } })).toBe(
      true,
    );
    expect(
      options.scrollRestoration({ location: { pathname: '/apidocs/v3' } }),
    ).toBe(false);
  });

  test('logs new queries and successful updates only', async () => {
    const { options } = createAndCapture();
    const queryClient = options.context.queryClient;
    const { debug } = logger('queryCache');
    const queryKey = [{ _id: 'getTeam', path: { team_key: 'frc254' } }];

    queryClient.setQueryData(queryKey, { key: 'frc254' });

    expect(debug).toHaveBeenCalledWith(
      { type: 'added', queryKey: 'getTeam', path: { team_key: 'frc254' } },
      'Query cache event',
    );
    expect(debug).toHaveBeenCalledWith(
      { type: 'updated', queryKey: 'getTeam', path: { team_key: 'frc254' } },
      'Query cache event',
    );

    debug.mockClear();
    await queryClient
      .fetchQuery({
        queryKey: [{ _id: 'failing' }],
        queryFn: () => Promise.reject(new Error('boom')),
        retry: false,
      })
      .catch(() => undefined);
    expect(debug).toHaveBeenCalledTimes(1);
    expect(debug).toHaveBeenCalledWith(
      { type: 'added', queryKey: 'failing', path: undefined },
      'Query cache event',
    );
  });

  test('skips browser-only setup on the server', () => {
    mocks.state.isServer = true;

    createAndCapture();

    expect(mocks.sentryInit).not.toHaveBeenCalled();
    expect(mocks.registerServiceWorker).not.toHaveBeenCalled();
    expect(mocks.subscribe).not.toHaveBeenCalled();
  });

  test('sets up Sentry and the service worker in the browser', () => {
    const { router } = createAndCapture();

    expect(mocks.tracingIntegration).toHaveBeenCalledWith(router);
    expect(mocks.sentryInit).toHaveBeenCalledWith(
      expect.objectContaining({
        dataCollection: expect.objectContaining({
          userInfo: false,
          cookies: false,
          httpBodies: [],
        }),
        integrations: [{ name: 'tracing' }],
        enabled: false,
      }),
    );
    expect(mocks.registerServiceWorker).toHaveBeenCalledTimes(1);
  });

  test('logs the initial page view when the browser is idle', async () => {
    const requestIdleCallback = vi.fn<(callback: () => void) => void>(
      (callback) => callback(),
    );
    vi.stubGlobal('requestIdleCallback', requestIdleCallback);

    createAndCapture();

    expect(requestIdleCallback).toHaveBeenCalledTimes(1);
    await waitFor(() =>
      expect(mocks.logEvent).toHaveBeenCalledWith(
        { name: 'analytics' },
        'page_view',
        {
          page_path: window.location.pathname,
          page_location: window.location.href,
          client_platform: 'pwa',
        },
      ),
    );
  });

  test('falls back to a timeout without requestIdleCallback', async () => {
    vi.useFakeTimers();
    try {
      Reflect.deleteProperty(window, 'requestIdleCallback');
      createAndCapture();

      expect(mocks.getAnalyticsInstance).not.toHaveBeenCalled();
      await vi.advanceTimersByTimeAsync(1);
    } finally {
      vi.useRealTimers();
    }

    await waitFor(() => expect(mocks.logEvent).toHaveBeenCalledTimes(1));
  });

  test('logs a page view on every resolved navigation', async () => {
    vi.stubGlobal('requestIdleCallback', vi.fn<() => void>());
    createAndCapture();

    expect(mocks.subscribe).toHaveBeenCalledWith(
      'onResolved',
      expect.any(Function),
    );
    const onResolved = mocks.subscribe.mock.calls[0][1] as ResolvedListener;
    onResolved({
      toLocation: { pathname: '/team/254', href: '/team/254?year=2026' },
    });

    await waitFor(() =>
      expect(mocks.logEvent).toHaveBeenCalledWith(
        { name: 'analytics' },
        'page_view',
        {
          page_path: '/team/254',
          page_location: '/team/254?year=2026',
          client_platform: 'pwa',
        },
      ),
    );
  });

  test('does not log page views when analytics is unavailable', async () => {
    mocks.getAnalyticsInstance.mockResolvedValue(null);
    vi.stubGlobal('requestIdleCallback', vi.fn<() => void>());
    createAndCapture();
    const onResolved = mocks.subscribe.mock.calls[0][1] as ResolvedListener;

    onResolved({ toLocation: { pathname: '/', href: '/' } });

    await waitFor(() =>
      expect(mocks.getAnalyticsInstance).toHaveBeenCalledTimes(1),
    );
    await Promise.resolve();
    expect(mocks.logEvent).not.toHaveBeenCalled();
  });
});

describe('router error components', () => {
  beforeEach(() => {
    mocks.createRouter.mockReturnValue({ isServer: true });
  });

  function errorComponent() {
    return createAndCapture().options.defaultErrorComponent;
  }

  test('renders the not-found page', () => {
    const { defaultNotFoundComponent: NotFound } = createAndCapture().options;

    render(<NotFound />);

    expect(
      screen.getByRole('heading', { name: 'Error 404 - Page Not Found' }),
    ).toBeTruthy();
  });

  test('logs, reports, and shows the stack for unexpected errors', () => {
    const ErrorComponent = errorComponent();
    const error = new Error('kaboom');

    render(<ErrorComponent error={error} reset={vi.fn<() => void>()} />);

    expect(logger('router').error).toHaveBeenCalledWith(error, 'Router error');
    expect(mocks.captureException).toHaveBeenCalledWith(error);
    expect(
      screen.getByRole('heading', { name: 'An error occurred.' }),
    ).toBeTruthy();
    expect(screen.getByText(/kaboom/, { selector: 'pre' })).toBeTruthy();
  });

  test('does not re-report ApiErrors to Sentry', () => {
    const ErrorComponent = errorComponent();

    render(
      <ErrorComponent
        error={new ApiError('Server Error', 500)}
        reset={vi.fn<() => void>()}
      />,
    );

    expect(mocks.captureException).not.toHaveBeenCalled();
  });

  test('wraps non-Error values in an Error', () => {
    const ErrorComponent = errorComponent();

    render(
      <ErrorComponent
        error={'plain string' as unknown as Error}
        reset={vi.fn<() => void>()}
      />,
    );

    expect(mocks.captureException).toHaveBeenCalledWith('plain string');
    // `new Error(String(error))` still has a stack, so the section shows.
    expect(
      screen.getByText(/Error: plain string/, { selector: 'pre' }),
    ).toBeTruthy();
  });

  test('omits the stack section for errors without a stack', () => {
    const ErrorComponent = errorComponent();
    const error = new Error('no stack');
    error.stack = undefined;

    render(<ErrorComponent error={error} reset={vi.fn<() => void>()} />);

    expect(
      screen.queryByRole('button', { name: /Copy stack trace/ }),
    ).toBeNull();
  });

  test('copies the stack trace and an agent prompt', async () => {
    const writeText = vi.fn<(text: string) => Promise<void>>();
    writeText.mockResolvedValue();
    vi.stubGlobal('navigator', { clipboard: { writeText } });
    const ErrorComponent = errorComponent();
    const error = new Error('kaboom');

    render(<ErrorComponent error={error} reset={vi.fn<() => void>()} />);

    fireEvent.click(screen.getByRole('button', { name: /Copy stack trace/ }));
    await waitFor(() =>
      expect(mocks.toastSuccess).toHaveBeenCalledWith(
        'Copied stack trace to clipboard!',
      ),
    );
    expect(writeText).toHaveBeenLastCalledWith(error.stack);

    fireEvent.click(
      screen.getByRole('button', { name: /Copy with agent prompt/ }),
    );
    await waitFor(() =>
      expect(mocks.toastSuccess).toHaveBeenCalledWith(
        'Copied agent prompt to clipboard!',
      ),
    );
    const prompt = writeText.mock.lastCall?.[0];
    expect(prompt).toContain('Please find the root cause.');
    expect(prompt).toContain(`URL: ${window.location.href}`);
    expect(prompt).toContain(`\`\`\`\n${error.stack}\n\`\`\``);
  });

  test('reports clipboard failures', async () => {
    const writeText = vi.fn<(text: string) => Promise<void>>();
    writeText.mockRejectedValue(new Error('denied'));
    vi.stubGlobal('navigator', { clipboard: { writeText } });
    const ErrorComponent = errorComponent();

    render(
      <ErrorComponent
        error={new Error('kaboom')}
        reset={vi.fn<() => void>()}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /Copy stack trace/ }));

    await waitFor(() =>
      expect(mocks.toastError).toHaveBeenCalledWith(
        'Failed to copy to clipboard.',
      ),
    );
  });
});
