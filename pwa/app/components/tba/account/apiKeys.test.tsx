import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type {
  ApiReadKeyMessage,
  ApiWriteKeyMessage,
} from '~/api/tba/mobile/types.gen';
import ApiKeysSection from '~/components/tba/account/apiKeys';

interface ApiKeysState {
  readKeys: ApiReadKeyMessage[];
  writeKeys: ApiWriteKeyMessage[];
  isLoading: boolean;
  addReadKey: (description: string) => Promise<unknown>;
  isAdding: boolean;
  deleteReadKey: (keyId: string) => Promise<unknown>;
  isDeleting: boolean;
}

const mocks = vi.hoisted(() => ({
  useApiKeys: vi.fn<() => ApiKeysState>(),
  addReadKey: vi.fn<(description: string) => Promise<unknown>>(),
  deleteReadKey: vi.fn<(keyId: string) => Promise<unknown>>(),
}));

vi.mock('~/lib/hooks/useApiKeys', () => ({ useApiKeys: mocks.useApiKeys }));

const READ_KEY: ApiReadKeyMessage = {
  key: 'read-key-1',
  description: 'Scouting app',
  created: '2026-03-01T12:34:56',
};
const WRITE_KEY: ApiWriteKeyMessage = {
  auth_id: 'auth-1',
  secret: 'secret-1',
  description: 'Event sync',
  event_keys: ['2026casj', '2026cafr'],
  auth_types: ['event teams', 'event matches'],
  expiration: '2026-04-01T00:00:00',
};

function renderSection(overrides: Partial<ApiKeysState> = {}) {
  mocks.useApiKeys.mockReturnValue({
    readKeys: [READ_KEY],
    writeKeys: [WRITE_KEY],
    isLoading: false,
    addReadKey: mocks.addReadKey,
    isAdding: false,
    deleteReadKey: mocks.deleteReadKey,
    isDeleting: false,
    ...overrides,
  });
  return render(<ApiKeysSection />);
}

function dialog() {
  return screen.queryByRole('dialog');
}

describe('ApiKeysSection', () => {
  test('shows loading states for both tables', () => {
    renderSection({ isLoading: true });

    expect(screen.getAllByText('Loading...')).toHaveLength(2);
  });

  test('shows empty states', () => {
    renderSection({ readKeys: [], writeKeys: [] });

    expect(screen.getByText('You have no read API keys yet.')).toBeTruthy();
    expect(screen.getByText('You have no write API keys.')).toBeTruthy();
  });

  test('lists read keys with their creation date', () => {
    renderSection();

    const row = screen.getByText('read-key-1').closest('tr');
    expect(
      [...(row?.querySelectorAll('td') ?? [])].map((cell) => cell.textContent),
    ).toEqual(['read-key-1', '2026-03-01', 'Scouting app', '']);
  });

  test('lists write keys with events, permissions, and expiry', () => {
    renderSection();

    const row = screen.getByText('auth-1').closest('tr');
    expect(
      [...(row?.querySelectorAll('td') ?? [])].map((cell) => cell.textContent),
    ).toEqual([
      '2026casj, 2026cafr',
      'event teams, event matches',
      '2026-04-01',
      'auth-1',
      'secret-1',
    ]);
    expect(
      screen
        .getByRole('link', { name: 'Request Write Key' })
        .getAttribute('href'),
    ).toBe('https://www.thebluealliance.com/request/apiwrite');
  });

  test('shows placeholders for missing dates and events, and raw unparseable dates', () => {
    renderSection({
      readKeys: [{ ...READ_KEY, created: null }],
      writeKeys: [{ ...WRITE_KEY, event_keys: [], expiration: 'not a date' }],
    });

    const readRow = screen.getByText('read-key-1').closest('tr');
    expect(readRow?.querySelectorAll('td')[1].textContent).toBe('—');
    const writeRow = screen.getByText('auth-1').closest('tr');
    expect(writeRow?.querySelectorAll('td')[0].textContent).toBe('—');
    expect(writeRow?.querySelectorAll('td')[2].textContent).toBe('not a date');
  });
});

describe('Adding a read key', () => {
  beforeEach(() => {
    renderSection();
    fireEvent.click(screen.getByRole('button', { name: 'Add Read Key' }));
  });

  function descriptionInput() {
    return screen.getByPlaceholderText('e.g. My scouting app');
  }

  test('requires a description', async () => {
    fireEvent.change(descriptionInput(), { target: { value: '   ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add Key' }));

    expect(await screen.findByText('A description is required.')).toBeTruthy();
    expect(mocks.addReadKey).not.toHaveBeenCalled();
  });

  test('adds a trimmed description and closes', async () => {
    mocks.addReadKey.mockResolvedValue(READ_KEY);
    fireEvent.change(descriptionInput(), {
      target: { value: '  Match scouting  ' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Add Key' }));

    await waitFor(() => expect(dialog()).toBeNull());
    expect(mocks.addReadKey).toHaveBeenCalledWith('Match scouting');
  });

  test('reports a failure and stays open', async () => {
    mocks.addReadKey.mockRejectedValue(new Error('nope'));
    fireEvent.change(descriptionInput(), { target: { value: 'Stats' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add Key' }));

    expect(
      await screen.findByText('Failed to add key. Please try again.'),
    ).toBeTruthy();
    expect(dialog()).toBeTruthy();
  });

  test('clears the form when reopened', async () => {
    fireEvent.change(descriptionInput(), { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add Key' }));
    await screen.findByText('A description is required.');

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    await waitFor(() => expect(dialog()).toBeNull());
    fireEvent.click(screen.getByRole('button', { name: 'Add Read Key' }));

    expect((descriptionInput() as HTMLInputElement).value).toBe('');
    expect(screen.queryByText('A description is required.')).toBeNull();
  });
});

describe('Adding a read key while a request is pending', () => {
  test('disables the add button', () => {
    renderSection({ isAdding: true });
    fireEvent.click(screen.getByRole('button', { name: 'Add Read Key' }));

    const button = screen.getByRole('button', { name: 'Adding...' });
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });
});

describe('Deleting a read key', () => {
  test('confirms with the key description and deletes', async () => {
    mocks.deleteReadKey.mockResolvedValue('read-key-1');
    renderSection();

    fireEvent.click(screen.getByRole('button', { name: 'Delete key' }));
    expect(
      screen.getByText(/permanently revoke the key "Scouting app"\./),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    await waitFor(() => expect(dialog()).toBeNull());
    expect(mocks.deleteReadKey).toHaveBeenCalledWith('read-key-1');
  });

  test('omits an empty description from the confirmation', () => {
    renderSection({ readKeys: [{ ...READ_KEY, description: '' }] });

    fireEvent.click(screen.getByRole('button', { name: 'Delete key' }));

    expect(screen.getByText(/permanently revoke the key\./)).toBeTruthy();
  });

  test('reports a failure, then clears it when reopened', async () => {
    mocks.deleteReadKey.mockRejectedValue(new Error('nope'));
    renderSection();

    fireEvent.click(screen.getByRole('button', { name: 'Delete key' }));
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    expect(
      await screen.findByText('Failed to delete key. Please try again.'),
    ).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    await waitFor(() => expect(dialog()).toBeNull());
    fireEvent.click(screen.getByRole('button', { name: 'Delete key' }));

    expect(
      screen.queryByText('Failed to delete key. Please try again.'),
    ).toBeNull();
  });

  test('disables the delete button while deleting', () => {
    renderSection({ isDeleting: true });

    fireEvent.click(screen.getByRole('button', { name: 'Delete key' }));

    const button = screen.getByRole('button', { name: 'Deleting...' });
    expect((button as HTMLButtonElement).disabled).toBe(true);
  });
});
