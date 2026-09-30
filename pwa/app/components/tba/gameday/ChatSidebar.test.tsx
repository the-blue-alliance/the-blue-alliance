import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { ChatSidebar } from '~/components/tba/gameday/ChatSidebar';
import type { WebcastWithMeta } from '~/lib/gameday/types';

const { useGamedayMock, setCurrentChat } = vi.hoisted(() => ({
  useGamedayMock: vi.fn<() => unknown>(),
  setCurrentChat: vi.fn<(channel: string) => void>(),
}));

vi.mock('~/lib/gameday/context', () => ({ useGameday: useGamedayMock }));

const WEBCASTS: Record<string, WebcastWithMeta> = {
  'fun-0': {
    id: 'fun-0',
    name: 'FUN',
    webcast: { type: 'twitch', channel: 'funroboticsnetwork' },
    isSpecial: true,
  },
  '2026miket-0': {
    id: '2026miket-0',
    name: 'Kettering #1',
    webcast: { type: 'twitch', channel: 'firstinmichigan' },
    isSpecial: false,
  },
  '2026casj-0': {
    id: '2026casj-0',
    name: 'Silicon Valley',
    webcast: { type: 'youtube', channel: 'abc123' },
    isSpecial: false,
  },
};

function renderSidebar(
  state: Partial<{
    chatSidebarVisible: boolean;
    currentChat: string;
    webcastsById: Record<string, WebcastWithMeta>;
  }> = {},
) {
  useGamedayMock.mockReturnValue({
    state: {
      chatSidebarVisible: true,
      currentChat: 'funroboticsnetwork',
      webcastsById: WEBCASTS,
      ...state,
    },
    setCurrentChat,
  });
  return render(<ChatSidebar />);
}

describe('ChatSidebar', () => {
  test('renders nothing when hidden', () => {
    const { container } = renderSidebar({ chatSidebarVisible: false });

    expect(container.innerHTML).toBe('');
  });

  test('embeds the current Twitch chat', () => {
    renderSidebar();

    expect(screen.getByTitle('Twitch chat').getAttribute('src')).toBe(
      `https://www.twitch.tv/embed/funroboticsnetwork/chat?parent=${window.location.hostname}&darkpopout`,
    );
    expect(screen.getByRole('button', { name: 'FUN' })).toBeTruthy();
  });

  test('prompts for a chat when none is selected', () => {
    renderSidebar({ currentChat: '' });

    expect(screen.getByText('No chat selected')).toBeTruthy();
    expect(screen.queryByTitle('Twitch chat')).toBeNull();
    expect(screen.getByRole('button', { name: 'Select a chat' })).toBeTruthy();
  });

  test('switches chat to another Twitch webcast', () => {
    renderSidebar();

    fireEvent.click(screen.getByRole('button', { name: 'FUN' }));

    const options = screen
      .getAllByRole('button')
      .map((button) => button.textContent);
    expect(options).toContain('FUN✓');
    expect(options).toContain('Kettering #1');
    expect(options).not.toContain('Silicon Valley');

    fireEvent.click(screen.getByRole('button', { name: 'Kettering #1' }));

    expect(setCurrentChat).toHaveBeenCalledWith('firstinmichigan');
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  test('explains when no Twitch chats are available', () => {
    renderSidebar({ currentChat: '', webcastsById: {} });

    fireEvent.click(screen.getByRole('button', { name: 'Select a chat' }));

    expect(screen.getByText('No Twitch chats available')).toBeTruthy();
  });
});
