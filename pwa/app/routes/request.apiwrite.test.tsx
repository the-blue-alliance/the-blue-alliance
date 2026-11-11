import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { beforeAll, beforeEach, describe, expect, test, vi } from 'vitest';

import type { ApiWriteKeyRequestResponse } from '~/api/tba/mobile/types.gen';
import { Route } from '~/routes/request.apiwrite';

const mocks = vi.hoisted(() => ({
  useAuth: vi.fn<() => unknown>(),
  requestApiWriteKey: vi.fn<(options: unknown) => Promise<unknown>>(),
}));

vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@tanstack/react-router')>();
  return {
    ...actual,
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
  };
});

vi.mock('~/components/tba/auth/auth', () => ({ useAuth: mocks.useAuth }));

vi.mock('~/components/tba/auth/loginPage', () => ({
  default: () => <h1>Please log in to your TBA Account</h1>,
}));

vi.mock('~/api/tba/mobile/sdk.gen', () => ({
  requestApiWriteKey: mocks.requestApiWriteKey,
}));

const USER = {
  email: 'volunteer@example.com',
  getIdToken: () => Promise.resolve('token-1'),
};

async function renderPage() {
  const Component = Route.options.component as () => ReactNode;
  render(
    <QueryClientProvider client={new QueryClient()}>
      <Component />
    </QueryClientProvider>,
  );
  await screen.findByRole('heading', { level: 1 });
}

function respondWith(status: ApiWriteKeyRequestResponse['status']) {
  mocks.requestApiWriteKey.mockResolvedValue({
    data: { code: 200, message: '', status },
  });
}

function fillAndSubmit() {
  fireEvent.change(screen.getByRole('textbox', { name: 'Event key' }), {
    target: { value: ' 2026cthar ' },
  });
  fireEvent.change(
    screen.getByRole('textbox', { name: 'Your role at the event' }),
    { target: { value: 'Scorekeeper' } },
  );
  fireEvent.click(screen.getByText('Match video'));
  fireEvent.click(screen.getByText('Event matches'));
  fireEvent.click(screen.getByRole('button', { name: 'Request Keys' }));
}

describe('request api write route', () => {
  beforeAll(async () => {
    await (
      Route.options.component as unknown as { preload: () => Promise<void> }
    ).preload();
  });

  beforeEach(() => {
    mocks.useAuth.mockReturnValue({ isInitialLoading: false, user: USER });
  });

  test('shows the sign-in page to a signed-out user', async () => {
    mocks.useAuth.mockReturnValue({ isInitialLoading: false, user: null });

    await renderPage();

    expect(
      screen.getByRole('heading', {
        name: 'Please log in to your TBA Account',
      }),
    ).toBeTruthy();
  });

  test('tells the user which email the result goes to', async () => {
    await renderPage();

    expect(screen.getByText('volunteer@example.com')).toBeTruthy();
  });

  test('sends the trimmed event key, role and checked permissions', async () => {
    respondWith('success');
    await renderPage();

    fillAndSubmit();

    await screen.findByText('Thanks!');
    expect(mocks.requestApiWriteKey).toHaveBeenCalledWith({
      auth: 'token-1',
      body: {
        event_key: '2026cthar',
        affiliation: 'Scorekeeper',
        auth_types: [1, 3],
      },
    });
  });

  test('clears the form after a successful request', async () => {
    respondWith('success');
    await renderPage();

    fillAndSubmit();

    await screen.findByText('Thanks!');
    expect(
      (screen.getByRole('textbox', { name: 'Event key' }) as HTMLInputElement)
        .value,
    ).toBe('');
  });

  test('links to the offseason suggestion form when the event is not on TBA', async () => {
    respondWith('bad_event');
    await renderPage();

    fillAndSubmit();

    await screen.findByText('Event not found');
    expect(
      screen
        .getAllByRole('link', { name: 'suggest it' })[0]
        .getAttribute('href'),
    ).toBe('/suggest/offseason');
  });

  test('asks for a role when the server reports none', async () => {
    respondWith('no_affiliation');
    await renderPage();

    fillAndSubmit();

    expect(await screen.findByText('Role required')).toBeTruthy();
  });

  test('shows a generic error when the request fails', async () => {
    mocks.requestApiWriteKey.mockRejectedValue(new Error('network'));
    await renderPage();

    fillAndSubmit();

    expect(await screen.findByText('Something went wrong')).toBeTruthy();
  });
});
