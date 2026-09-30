import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import type { ReactNode } from 'react';
import {
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  test,
  vi,
} from 'vitest';

import type { SearchIndex } from '~/api/tba/read';
import { SearchModal } from '~/components/tba/navigation/searchModal';

const { useNavigateMock, searchIndexMock } = vi.hoisted(() => ({
  useNavigateMock: vi.fn<(options: { to: string }) => void>(),
  searchIndexMock: vi.fn<() => Promise<SearchIndex>>(),
}));

vi.mock('~/api/tba/read/@tanstack/react-query.gen', () => ({
  getSearchIndexOptions: () => ({
    queryKey: ['searchIndex'],
    queryFn: searchIndexMock,
  }),
}));

const SEARCH_INDEX: SearchIndex = {
  teams: [
    { key: 'frc254', nickname: 'The Cheesy Poofs' },
    { key: 'frc1678', nickname: 'Citrus Circuits' },
  ],
  events: [
    { key: '2026casj', name: 'Silicon Valley Regional' },
    { key: '2025cmptx', name: 'Einstein Field' },
  ],
};

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => useNavigateMock,
  ClientOnly: ({ children }: { children: ReactNode }) => children,
}));

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver = ResizeObserverMock;
  // cmdk scrolls the highlighted item into view; jsdom lacks the API.
  Element.prototype.scrollIntoView = () => undefined;
});

function renderSearchModal() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <SearchModal />
    </QueryClientProvider>,
  );
}

describe('SearchModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    searchIndexMock.mockResolvedValue(SEARCH_INDEX);
  });

  afterEach(() => {
    cleanup();
    document.body.innerHTML = '';
  });

  test('focuses the search text box when opened via mouse click', async () => {
    renderSearchModal();

    const desktopTrigger = screen.getByRole('button', {
      name: /search teams and events/i,
    });
    fireEvent.pointerDown(desktopTrigger, { pointerType: 'mouse' });
    fireEvent.click(desktopTrigger, { pointerType: 'mouse' });

    const input = await screen.findByPlaceholderText(
      'Search teams and events...',
    );
    await vi.waitFor(() => {
      expect(document.activeElement).toBe(input);
    });
  });

  test('focuses the search text box when opened via touch', async () => {
    renderSearchModal();

    const mobileTrigger = screen.getByRole('button', { name: 'Search' });

    fireEvent.pointerDown(mobileTrigger, { pointerType: 'touch' });
    fireEvent.click(mobileTrigger, { pointerType: 'touch', detail: 1 });

    const input = await screen.findByPlaceholderText(
      'Search teams and events...',
    );
    await vi.waitFor(() => {
      expect(document.activeElement).toBe(input);
    });
  });

  async function openAndType(query: string) {
    renderSearchModal();
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    const input = await screen.findByPlaceholderText(
      'Search teams and events...',
    );
    fireEvent.change(input, { target: { value: query } });
    return input;
  }

  test('toggles with Cmd/Ctrl+K and slash', async () => {
    renderSearchModal();

    fireEvent.keyDown(document, { key: 'k', metaKey: true });
    expect(
      await screen.findByPlaceholderText('Search teams and events...'),
    ).toBeTruthy();

    fireEvent.keyDown(document.body, { key: 'k', ctrlKey: true });
    await waitFor(() =>
      expect(
        screen.queryByPlaceholderText('Search teams and events...'),
      ).toBeNull(),
    );

    fireEvent.keyDown(document.body, { key: '/' });
    expect(
      await screen.findByPlaceholderText('Search teams and events...'),
    ).toBeTruthy();
  });

  test('ignores shortcuts typed into form fields', () => {
    renderSearchModal();
    const fields: HTMLElement[] = [
      document.createElement('input'),
      document.createElement('textarea'),
      document.createElement('select'),
    ];
    const editable = document.createElement('div');
    editable.contentEditable = 'true';
    // jsdom does not implement isContentEditable.
    Object.defineProperty(editable, 'isContentEditable', { value: true });
    fields.push(editable);

    for (const field of fields) {
      document.body.append(field);
      fireEvent.keyDown(field, { key: '/' });
    }
    fireEvent.keyDown(document.body, { key: 'k' });

    expect(
      screen.queryByPlaceholderText('Search teams and events...'),
    ).toBeNull();
  });

  test('shows the Ctrl shortcut off macOS and ⌘ on macOS', () => {
    renderSearchModal();
    expect(screen.getByText('Ctrl')).toBeTruthy();
    cleanup();

    vi.spyOn(navigator, 'userAgent', 'get').mockReturnValue(
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    );
    renderSearchModal();
    expect(screen.getByText('⌘')).toBeTruthy();
  });

  test('shows a loading state until the index arrives', async () => {
    searchIndexMock.mockReturnValue(new Promise(() => undefined));
    renderSearchModal();

    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    expect(await screen.findByTestId('search-index-loading')).toBeTruthy();
  });

  test('shows an error when the index fails to load', async () => {
    searchIndexMock.mockRejectedValue(new Error('offline'));
    renderSearchModal();

    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    expect(await screen.findByTestId('search-index-error')).toBeTruthy();
  });

  test('says when nothing matches', async () => {
    await openAndType('zzzzzz');

    expect(await screen.findByText('No results found.')).toBeTruthy();
  });

  test('lists teams first for a team query and navigates to the team', async () => {
    await openAndType('254');

    const team = await screen.findByText('254 - The Cheesy Poofs');
    const headings = screen
      .getAllByText(/^(Teams|Events)$/)
      .map((heading) => heading.textContent);
    expect(headings[0]).toBe('Teams');

    fireEvent.click(team);

    expect(useNavigateMock).toHaveBeenCalledWith({ to: '/team/254' });
    await waitFor(() =>
      expect(
        screen.queryByPlaceholderText('Search teams and events...'),
      ).toBeNull(),
    );
  });

  test('lists events first for an event query and navigates to the event', async () => {
    await openAndType('Silicon Valley');

    const event = await screen.findByText(/Silicon Valley Regional/);
    expect(event.textContent).toBe('2026 Silicon Valley Regional [casj]');
    expect(screen.queryByText('Teams')).toBeNull();

    fireEvent.click(event);

    expect(useNavigateMock).toHaveBeenCalledWith({ to: '/event/2026casj' });
  });
});
