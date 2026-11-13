import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { Webhook } from '~/api/tba/mobile/types.gen';
import WebhooksSection from '~/components/tba/account/webhooks';

type Action = (...args: never[]) => Promise<unknown>;

const mocks = vi.hoisted(() => ({
  useWebhooks: vi.fn<() => unknown>(),
  addWebhook: vi.fn<Action>(),
  verifyWebhook: vi.fn<Action>(),
  resendVerification: vi.fn<Action>(),
  deleteWebhook: vi.fn<Action>(),
  pingWebhook: vi.fn<Action>(),
  toastSuccess: vi.fn<(message: string) => void>(),
  toastError: vi.fn<(message: string) => void>(),
}));

vi.mock('~/lib/hooks/useWebhooks', () => ({ useWebhooks: mocks.useWebhooks }));

vi.mock('sonner', () => ({
  toast: { success: mocks.toastSuccess, error: mocks.toastError },
}));

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children?: ReactNode;
    to: string;
  }) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

const UNVERIFIED: Webhook = {
  webhook_id: '1',
  name: 'Scouting',
  url: 'https://scouting.example.com/hook',
  secret: 'secret-1',
  verified: false,
};
const VERIFIED: Webhook = {
  webhook_id: '2',
  name: 'Stats',
  url: 'https://stats.example.com/hook',
  secret: 'secret-2',
  verified: true,
};

function renderSection(
  webhooks: Webhook[] = [UNVERIFIED, VERIFIED],
  isLoading = false,
) {
  mocks.useWebhooks.mockReturnValue({
    webhooks,
    isLoading,
    addWebhook: mocks.addWebhook,
    verifyWebhook: mocks.verifyWebhook,
    resendVerification: mocks.resendVerification,
    deleteWebhook: mocks.deleteWebhook,
    pingWebhook: mocks.pingWebhook,
  });
  render(<WebhooksSection />);
}

function row(name: string) {
  const cell = screen.getByRole('cell', { name });
  return cell.closest('tr') as HTMLElement;
}

function dialog() {
  return screen.queryByRole('dialog');
}

describe('WebhooksSection', () => {
  test('shows a loading message', () => {
    renderSection([], true);

    expect(screen.getByText('Loading...')).toBeTruthy();
  });

  test('says when there are no webhooks', () => {
    renderSection([]);

    expect(screen.getByText('You have no webhooks yet.')).toBeTruthy();
  });

  test('shows each webhook secret', () => {
    renderSection();

    expect(row('Scouting').textContent).toContain('secret-1');
  });

  test('shows a verified webhook as verified', () => {
    renderSection();

    expect(row('Stats').textContent).toContain('Verified');
  });

  test('offers to verify an unverified webhook', () => {
    renderSection();

    expect(
      screen
        .getAllByRole('button', { name: 'Verify' })
        .map((b) => b.closest('tr')),
    ).toEqual([row('Scouting')]);
  });

  test('links to the webhook docs', () => {
    renderSection();

    expect(
      screen.getByRole('link', { name: 'webhook docs' }).getAttribute('href'),
    ).toBe('/apidocs/webhooks');
  });
});

describe('Adding a webhook', () => {
  beforeEach(() => {
    renderSection([]);
    fireEvent.click(screen.getByRole('button', { name: 'Add Webhook' }));
  });

  function fill(name: string, url: string) {
    fireEvent.change(screen.getByRole('textbox', { name: 'Name' }), {
      target: { value: name },
    });
    fireEvent.change(screen.getByRole('textbox', { name: 'URL' }), {
      target: { value: url },
    });
    fireEvent.click(
      screen.getAllByRole('button', { name: 'Add Webhook' }).at(-1) as Element,
    );
  }

  test('requires a name and URL', async () => {
    fill('Hook', '  ');

    expect(await screen.findByText('Enter a name and a URL.')).toBeTruthy();
  });

  test('sends the trimmed name and URL', async () => {
    mocks.addWebhook.mockResolvedValue(UNVERIFIED);

    fill(' Hook ', ' https://example.com/hook ');

    await waitFor(() =>
      expect(mocks.addWebhook).toHaveBeenCalledWith({
        name: 'Hook',
        url: 'https://example.com/hook',
      }),
    );
  });

  test('closes after adding', async () => {
    mocks.addWebhook.mockResolvedValue(UNVERIFIED);

    fill('Hook', 'https://example.com/hook');

    await waitFor(() => expect(dialog()).toBeNull());
  });

  test('says a verification code was sent', async () => {
    mocks.addWebhook.mockResolvedValue(UNVERIFIED);

    fill('Hook', 'https://example.com/hook');

    await waitFor(() =>
      expect(mocks.toastSuccess).toHaveBeenCalledWith(
        expect.stringContaining('We sent a verification code'),
      ),
    );
  });

  test('reports a failure', async () => {
    mocks.addWebhook.mockRejectedValue(new Error('nope'));

    fill('Hook', 'https://example.com/hook');

    expect(
      await screen.findByText('Failed to add webhook. Please try again.'),
    ).toBeTruthy();
  });
});

describe('Verifying a webhook', () => {
  beforeEach(() => {
    renderSection();
    fireEvent.click(screen.getByRole('button', { name: 'Verify' }));
  });

  function submit(code: string) {
    fireEvent.change(
      screen.getByRole('textbox', { name: 'Verification code' }),
      { target: { value: code } },
    );
    fireEvent.click(
      screen.getAllByRole('button', { name: 'Verify' }).at(-1) as Element,
    );
  }

  test('sends the code for that webhook', async () => {
    mocks.verifyWebhook.mockResolvedValue('1');

    submit(' abc123 ');

    await waitFor(() =>
      expect(mocks.verifyWebhook).toHaveBeenCalledWith({
        webhook_id: '1',
        code: 'abc123',
      }),
    );
  });

  test('closes after a correct code', async () => {
    mocks.verifyWebhook.mockResolvedValue('1');

    submit('abc123');

    await waitFor(() => expect(dialog()).toBeNull());
  });

  test('explains a wrong code', async () => {
    mocks.verifyWebhook.mockRejectedValue(new Error('Incorrect'));

    submit('wrong');

    expect(await screen.findByText(/That code did not work/)).toBeTruthy();
  });

  test('requires a code', async () => {
    submit(' ');

    expect(
      await screen.findByText('Enter the verification code.'),
    ).toBeTruthy();
  });
});

describe('Webhook row actions', () => {
  test('pings the webhook URL', async () => {
    mocks.pingWebhook.mockResolvedValue(undefined);
    renderSection([VERIFIED]);

    fireEvent.click(screen.getByRole('button', { name: 'Ping' }));

    await waitFor(() =>
      expect(mocks.toastSuccess).toHaveBeenCalledWith('Sent a ping to Stats.'),
    );
  });

  test('reports a failed ping', async () => {
    mocks.pingWebhook.mockRejectedValue(new Error('nope'));
    renderSection([VERIFIED]);

    fireEvent.click(screen.getByRole('button', { name: 'Ping' }));

    await waitFor(() =>
      expect(mocks.toastError).toHaveBeenCalledWith(
        'Could not send a ping to Stats.',
      ),
    );
  });

  test('sends a new verification code', async () => {
    mocks.resendVerification.mockResolvedValue('1');
    renderSection([UNVERIFIED]);

    fireEvent.click(screen.getByRole('button', { name: 'Resend Code' }));

    await waitFor(() =>
      expect(mocks.toastSuccess).toHaveBeenCalledWith(
        'Sent a new verification code to Scouting.',
      ),
    );
  });

  test('reports a failed resend', async () => {
    mocks.resendVerification.mockRejectedValue(new Error('nope'));
    renderSection([UNVERIFIED]);

    fireEvent.click(screen.getByRole('button', { name: 'Resend Code' }));

    await waitFor(() =>
      expect(mocks.toastError).toHaveBeenCalledWith(
        'Could not send a new code to Scouting.',
      ),
    );
  });

  test('deletes a webhook after confirming', async () => {
    mocks.deleteWebhook.mockResolvedValue('2');
    renderSection([VERIFIED]);

    fireEvent.click(screen.getByRole('button', { name: 'Delete Stats' }));
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    await waitFor(() => expect(mocks.deleteWebhook).toHaveBeenCalledWith('2'));
  });

  test('reports a failed delete', async () => {
    mocks.deleteWebhook.mockRejectedValue(new Error('nope'));
    renderSection([VERIFIED]);

    fireEvent.click(screen.getByRole('button', { name: 'Delete Stats' }));
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    expect(
      await screen.findByText('Failed to delete webhook. Please try again.'),
    ).toBeTruthy();
  });
});
