import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
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

import { SearchModal } from '~/components/tba/navigation/searchModal';

const { useNavigateMock } = vi.hoisted(() => ({
  useNavigateMock: vi.fn<() => void>(),
}));

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
});
