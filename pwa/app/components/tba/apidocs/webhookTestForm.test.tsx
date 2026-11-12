import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { Webhook } from '~/api/tba/mobile/types.gen';
import WebhookTestForm from '~/components/tba/apidocs/webhookTestForm';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn<() => unknown>(),
  useWebhooks: vi.fn<() => unknown>(),
  sendTest: vi.fn<(body: unknown) => Promise<unknown>>(),
}));

vi.mock('~/components/tba/auth/auth', () => ({ useAuth: mocks.useAuth }));
vi.mock('~/lib/hooks/useWebhooks', () => ({ useWebhooks: mocks.useWebhooks }));

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
  name: 'Draft',
  url: 'https://draft.example.com',
  secret: 's1',
  verified: false,
};
const SCOUTING: Webhook = {
  webhook_id: '2',
  name: 'Scouting',
  url: 'https://scouting.example.com',
  secret: 's2',
  verified: true,
};
const STATS: Webhook = {
  webhook_id: '3',
  name: 'Stats',
  url: 'https://stats.example.com',
  secret: 's3',
  verified: true,
};

function renderForm(webhooks: Webhook[] = [UNVERIFIED, SCOUTING, STATS]) {
  mocks.useWebhooks.mockReturnValue({
    webhooks,
    isLoading: false,
    sendTest: mocks.sendTest,
  });
  render(
    <WebhookTestForm
      notificationType="schedule_updated"
      label="Event Schedule Updated"
      eventKey="2014necmp"
      matchKey="2014necmp_f1m1"
    />,
  );
}

function sendButton() {
  return screen.getByRole('button', {
    name: 'Send test Event Schedule Updated',
  });
}

describe('WebhookTestForm signed out', () => {
  test('asks the user to sign in', () => {
    mocks.useAuth.mockReturnValue({ isInitialLoading: false, user: null });

    renderForm();

    expect(
      screen.getByRole('link', { name: 'Sign in' }).getAttribute('href'),
    ).toBe('/account');
  });
});

describe('WebhookTestForm signed in', () => {
  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ isInitialLoading: false, user: {} });
  });

  test('points to the account page when no webhook is verified', () => {
    renderForm([UNVERIFIED]);

    expect(screen.getByText(/You have no verified webhooks/)).toBeTruthy();
  });

  test('fills in the sample keys', () => {
    renderForm();

    expect(
      (screen.getByRole('textbox', { name: 'Match key' }) as HTMLInputElement)
        .value,
    ).toBe('2014necmp_f1m1');
  });

  test('sends to the first verified webhook by default', async () => {
    mocks.sendTest.mockResolvedValue(undefined);
    renderForm();

    fireEvent.click(sendButton());

    await waitFor(() =>
      expect(mocks.sendTest).toHaveBeenCalledWith({
        webhook_id: '2',
        notification_type: 'schedule_updated',
        event_key: '2014necmp',
        match_key: '2014necmp_f1m1',
      }),
    );
  });

  test('sends to the chosen webhook', async () => {
    mocks.sendTest.mockResolvedValue(undefined);
    renderForm();

    fireEvent.click(screen.getByRole('combobox', { name: 'Send to' }));
    fireEvent.keyDown(await screen.findByRole('option', { name: 'Stats' }), {
      key: 'Enter',
    });
    fireEvent.click(sendButton());

    await waitFor(() =>
      expect(mocks.sendTest).toHaveBeenCalledWith(
        expect.objectContaining({ webhook_id: '3' }),
      ),
    );
  });

  test('sends edited keys', async () => {
    mocks.sendTest.mockResolvedValue(undefined);
    renderForm();

    fireEvent.change(screen.getByRole('textbox', { name: 'Event key' }), {
      target: { value: ' 2024casj ' },
    });
    fireEvent.click(sendButton());

    await waitFor(() =>
      expect(mocks.sendTest).toHaveBeenCalledWith(
        expect.objectContaining({ event_key: '2024casj' }),
      ),
    );
  });

  test('says when the test was sent', async () => {
    mocks.sendTest.mockResolvedValue(undefined);
    renderForm();

    fireEvent.click(sendButton());

    expect((await screen.findByRole('status')).textContent).toBe('Sent.');
  });

  test('shows the error when the test fails', async () => {
    mocks.sendTest.mockRejectedValue(new Error('Webhook is not verified'));
    renderForm();

    fireEvent.click(sendButton());

    expect((await screen.findByRole('status')).textContent).toBe(
      'Webhook is not verified',
    );
  });
});
