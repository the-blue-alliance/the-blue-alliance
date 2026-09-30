import { QueryClient } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import type { ComponentType, ReactNode } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

type Interceptor = (...args: never[]) => unknown;

const mocks = vi.hoisted(() => ({
  pathname: '/',
  loggerDebug: vi.fn<(data: unknown, message: string) => void>(),
  createCachedFetch: vi.fn<(options: unknown) => unknown>(),
}));

const clients = vi.hoisted(() => {
  function createClientMock() {
    return {
      interceptors: {
        request: { use: vi.fn<(fn: Interceptor) => void>() },
        error: { use: vi.fn<(fn: Interceptor) => void>() },
      },
      setConfig: vi.fn<(config: unknown) => void>(),
    };
  }
  return {
    read: createClientMock(),
    mobile: createClientMock(),
    moderation: createClientMock(),
    colors: createClientMock(),
  };
});

function passThrough({ children }: { children?: ReactNode }) {
  return <>{children}</>;
}

vi.mock('@tanstack/react-router', () => ({
  createRootRouteWithContext: () => (options: unknown) => ({ options }),
  HeadContent: () => <meta name="head-content" />,
  Scripts: () => <span data-testid="scripts" />,
  Outlet: () => <main>Outlet</main>,
  useLocation: () => ({ pathname: mocks.pathname }),
}));

vi.mock('~/api/tba/read/client.gen', () => ({
  client: clients.read,
}));
vi.mock('~/api/tba/mobile/client.gen', () => ({
  client: clients.mobile,
}));
vi.mock('~/api/tba/moderation/client.gen', () => ({
  client: clients.moderation,
}));
vi.mock('~/api/colors/client.gen', () => ({
  client: clients.colors,
}));

vi.mock('~/api/tba/read/@tanstack/react-query.gen', () => ({
  getStatusOptions: () => ({ queryKey: ['status'] }),
  getSearchIndexOptions: () => ({ queryKey: ['searchIndex'] }),
}));

vi.mock('~/lib/logger', () => ({
  createLogger: () => ({ debug: mocks.loggerDebug }),
}));

vi.mock('~/lib/middleware/network-cache', () => ({
  createCachedFetch: mocks.createCachedFetch,
}));

vi.mock('~/components/tba/auth/auth', () => ({
  AuthContextProvider: passThrough,
}));
vi.mock('~/components/tba/match/matchModal', () => ({
  MatchModal: () => <div>Match modal</div>,
}));
vi.mock('~/components/tba/navigation/footer', () => ({
  Footer: () => <footer>Footer</footer>,
}));
vi.mock('~/components/tba/navigation/navbar', () => ({
  Navbar: () => <nav>Navbar</nav>,
}));
vi.mock('~/components/tba/tableOfContents', () => ({
  TOCRendererProvider: passThrough,
}));
vi.mock('~/components/ui/sonner', () => ({ Toaster: () => null }));
vi.mock('~/components/ui/tooltip', () => ({ TooltipProvider: passThrough }));
vi.mock('~/lib/theme', () => ({ ThemeProvider: passThrough }));

vi.mock('@tanstack/react-router-devtools', () => ({
  TanStackRouterDevtools: () => <div>Router devtools</div>,
}));
vi.mock('@tanstack/react-query-devtools', () => ({
  ReactQueryDevtools: () => <div>Query devtools</div>,
}));

interface RootOptions {
  beforeLoad: (args: {
    context: { queryClient: QueryClient };
  }) => Promise<{ status: unknown; currentSeason: number }>;
  head: (args: { matches: { pathname: string }[] }) => {
    meta: Record<string, string>[];
    links: Record<string, string>[];
  };
  validateSearch: { parse: (value: unknown) => unknown };
  component: ComponentType;
}

async function loadRoot() {
  vi.resetModules();
  const module = await import('~/routes/__root');
  return (module.Route as unknown as { options: RootOptions }).options;
}

function registered<T extends Interceptor>(
  use: (typeof clients.read)['interceptors']['error']['use'],
) {
  return use.mock.calls[0][0] as unknown as T;
}

function renderRoot(Component: ComponentType) {
  // RootComponent renders <html>; mount it as the document's children.
  return render(<Component />, { container: document });
}

describe('root route module setup', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_TBA_API_READ_KEY', 'read-key');
    vi.stubEnv('VITE_TBA_MOBILE_API_BASE_URL', '');
    vi.stubEnv('VITE_TBA_MODERATION_API_BASE_URL', '');
  });

  test('adds the read key to every TBA API request', async () => {
    await loadRoot();
    const onRequest = registered<(request: Request) => Request>(
      clients.read.interceptors.request.use,
    );
    const request = new Request(
      'https://www.thebluealliance.com/api/v3/status',
    );

    expect(onRequest(request)).toBe(request);
    expect(request.headers.get('X-TBA-Auth-Key')).toBe('read-key');
    expect(mocks.loggerDebug).toHaveBeenCalledWith(
      {
        method: 'GET',
        url: 'https://www.thebluealliance.com/api/v3/status',
      },
      'Sending request to TBA API',
    );
  });

  test('maps HTTP failures to ApiErrors on the read, colors, and moderation clients', async () => {
    await loadRoot();
    const { ApiError } = await import('~/lib/apiError');
    const failed = new Response(null, { status: 404, statusText: 'Not Found' });

    for (const client of [clients.read, clients.colors, clients.moderation]) {
      const onError = registered<
        (error: unknown, response: Response) => unknown
      >(client.interceptors.error.use);
      const mapped = onError({ Error: 'missing' }, failed);
      expect(mapped).toBeInstanceOf(ApiError);
      expect(mapped).toMatchObject({ status: 404, message: 'Not Found' });
    }
  });

  test('leaves the browser fetch and default base URLs alone', async () => {
    await loadRoot();

    expect(clients.read.setConfig).not.toHaveBeenCalled();
    expect(clients.mobile.setConfig).not.toHaveBeenCalled();
    expect(clients.moderation.setConfig).not.toHaveBeenCalled();
  });

  test('points the mobile and moderation clients at configured backends', async () => {
    vi.stubEnv('VITE_TBA_MOBILE_API_BASE_URL', 'http://localhost:8080/mobile');
    vi.stubEnv('VITE_TBA_MODERATION_API_BASE_URL', 'http://localhost:8080/mod');

    await loadRoot();

    expect(clients.mobile.setConfig).toHaveBeenCalledWith({
      baseUrl: 'http://localhost:8080/mobile',
    });
    expect(clients.moderation.setConfig).toHaveBeenCalledWith({
      baseUrl: 'http://localhost:8080/mod',
    });
  });

  test('installs the network cache when rendering on the server', async () => {
    const cachedFetch = vi.fn<typeof fetch>();
    mocks.createCachedFetch.mockReturnValue(cachedFetch);
    vi.stubGlobal('window', undefined);

    await loadRoot();

    expect(mocks.createCachedFetch).toHaveBeenCalledWith({
      cacheableMethods: ['GET'],
    });
    expect(clients.read.setConfig).toHaveBeenCalledWith({
      fetch: cachedFetch,
    });
  });
});

describe('root route options', () => {
  test('validates the global match modal search param', async () => {
    const { validateSearch } = await loadRoot();

    expect(validateSearch.parse({ matchKey: '2026casj_qm1' })).toEqual({
      matchKey: '2026casj_qm1',
    });
    expect(validateSearch.parse({})).toEqual({});
  });

  test('loads status once and prefetches the search index', async () => {
    const { beforeLoad } = await loadRoot();
    const queryClient = new QueryClient();
    const status = { current_season: 2026, max_season: 2026 };
    const ensureQueryData = vi
      .spyOn(queryClient, 'ensureQueryData')
      .mockResolvedValue(status);
    const prefetchQuery = vi
      .spyOn(queryClient, 'prefetchQuery')
      .mockResolvedValue();

    await expect(beforeLoad({ context: { queryClient } })).resolves.toEqual({
      status,
      currentSeason: 2026,
    });
    expect(ensureQueryData).toHaveBeenCalledWith({
      queryKey: ['status'],
      staleTime: expect.any(Number),
    });
    expect(prefetchQuery).toHaveBeenCalledWith({
      queryKey: ['searchIndex'],
      staleTime: expect.any(Number),
    });
  });

  test('falls back to the calendar year without a current season', async () => {
    vi.stubEnv('SSR', true);
    const { beforeLoad } = await loadRoot();
    const queryClient = new QueryClient();
    vi.spyOn(queryClient, 'ensureQueryData').mockResolvedValue({
      current_season: null,
    });
    const prefetchQuery = vi.spyOn(queryClient, 'prefetchQuery');

    const context = await beforeLoad({ context: { queryClient } });

    expect(context.currentSeason).toBe(new Date().getFullYear());
    expect(prefetchQuery).not.toHaveBeenCalled();
  });

  test('builds head tags with a canonical link for the deepest match', async () => {
    const { head } = await loadRoot();

    const tags = head({
      matches: [{ pathname: '/' }, { pathname: '/team/254' }],
    });

    expect(tags.meta).toContainEqual({ title: 'The Blue Alliance' });
    expect(tags.links).toContainEqual({
      rel: 'canonical',
      href: 'https://www.thebluealliance.com/team/254',
    });
    expect(tags.links).toContainEqual({
      rel: 'manifest',
      href: '/manifest.webmanifest',
    });
  });
});

describe('RootComponent', () => {
  beforeEach(() => {
    mocks.pathname = '/';
    document.body.removeAttribute('data-hydrated');
  });

  test('renders the site chrome around the outlet', async () => {
    const { component: Root } = await loadRoot();

    renderRoot(Root);

    expect(screen.getByText('Navbar')).toBeTruthy();
    expect(screen.getByText('Footer')).toBeTruthy();
    expect(screen.getByText('Match modal')).toBeTruthy();
    expect(
      screen.getByRole('main').parentElement?.parentElement?.className,
    ).toContain('container');
    expect(document.body.getAttribute('data-hydrated')).toBe('true');
    expect(await screen.findByText('Router devtools')).toBeTruthy();
    expect(await screen.findByText('Query devtools')).toBeTruthy();
  });

  test('drops the container on full-width routes', async () => {
    mocks.pathname = '/match_suggestion';
    const { component: Root } = await loadRoot();

    renderRoot(Root);

    expect(screen.getByText('Navbar')).toBeTruthy();
    expect(
      screen.getByRole('main').parentElement?.parentElement?.className,
    ).not.toContain('container');
  });

  test('renders only the outlet on full-screen routes', async () => {
    mocks.pathname = '/gameday';
    const { component: Root } = await loadRoot();

    const { rerender } = renderRoot(Root);
    rerender(<Root />);

    expect(screen.getByText('Outlet')).toBeTruthy();
    expect(screen.queryByText('Navbar')).toBeNull();
    expect(screen.queryByText('Footer')).toBeNull();
    await waitFor(() =>
      expect(screen.getByText('Router devtools')).toBeTruthy(),
    );
  });
});
