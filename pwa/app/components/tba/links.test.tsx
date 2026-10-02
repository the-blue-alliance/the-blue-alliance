import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import type { Event, Match, Team } from '~/api/tba/read';
import {
  getEventQueryKey,
  getMatchQueryKey,
} from '~/api/tba/read/@tanstack/react-query.gen';
import {
  DistrictLink,
  EventLink,
  EventLocationLink,
  MatchLink,
  PitLocationLink,
  TeamLink,
  TeamLocationLink,
} from '~/components/tba/links';

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    to,
    params,
    search,
    mask,
    replace,
    resetScroll,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children?: ReactNode;
    to: string;
    params?: Record<string, string | undefined>;
    search?: (prev: Record<string, string>) => Record<string, string>;
    mask?: { to: string; params: Record<string, string> };
    replace?: boolean;
    resetScroll?: boolean;
  }) => (
    <a
      href={to}
      data-params={JSON.stringify(params ?? {})}
      data-search={
        search ? JSON.stringify(search({ tab: 'results' })) : undefined
      }
      data-mask={mask ? JSON.stringify(mask) : undefined}
      data-replace={replace === undefined ? undefined : String(replace)}
      data-reset-scroll={
        resetScroll === undefined ? undefined : String(resetScroll)
      }
      {...props}
    >
      {children}
    </a>
  ),
}));

const event = {
  key: '2026miket',
  location_name: 'Kettering University',
  address: '1700 University Ave',
  city: 'Flint',
  state_prov: 'MI',
  country: 'USA',
} as Event;

const team = {
  key: 'frc254',
  team_number: 254,
  city: 'San Jose',
  state_prov: 'California',
  country: 'USA',
} as Team;

describe('PitLocationLink', () => {
  test('renders the pit location as a Nexus link', () => {
    render(
      <PitLocationLink
        teamNumber={254}
        year={2026}
        firstEventCode="cmptx"
        pitLocation="A1"
      />,
    );

    const link = screen.getByRole('link', { name: 'A1' });
    expect(link.getAttribute('href')).toBe(
      'https://frc.nexus/en/event/2026cmptx/team/254/map',
    );
  });
});

describe('TeamLink', () => {
  test('links a team key to the team page for a year', () => {
    render(
      <TeamLink teamOrKey="frc604" year={2025}>
        604
      </TeamLink>,
    );
    const link = screen.getByRole('link', { name: '604' });
    expect(link.getAttribute('href')).toBe('/team/$teamNumber/{-$year}');
    expect(link.dataset.params).toBe('{"teamNumber":"604","year":"2025"}');
    expect(link.className).toBe('text-foreground hover:underline');
  });

  test('links a team object without a year and keeps a custom class', () => {
    render(
      <TeamLink teamOrKey={team} className="font-bold">
        254
      </TeamLink>,
    );
    const link = screen.getByRole('link', { name: '254' });
    expect(link.dataset.params).toBe('{"teamNumber":"254"}');
    expect(link.className).toBe('font-bold');
  });

  test('links year 0 to the team history page', () => {
    render(
      <TeamLink teamOrKey="frc254" year={0}>
        history
      </TeamLink>,
    );
    const link = screen.getByRole('link', { name: 'history' });
    expect(link.getAttribute('href')).toBe('/team/$teamNumber/history');
    expect(link.dataset.params).toBe('{"teamNumber":"254"}');
    expect(link.className).toBe('text-foreground hover:underline');
  });

  test('keeps a custom class on the history link', () => {
    render(
      <TeamLink teamOrKey="frc254" year={0} className="font-bold">
        history
      </TeamLink>,
    );
    expect(screen.getByRole('link', { name: 'history' }).className).toBe(
      'font-bold',
    );
  });
});

describe('EventLink', () => {
  test.each([
    ['key', '2026miket'],
    ['object', event],
  ] as const)('links an event %s', (_, eventOrKey) => {
    render(<EventLink eventOrKey={eventOrKey}>Event</EventLink>);
    const link = screen.getByRole('link', { name: 'Event' });
    expect(link.getAttribute('href')).toBe('/event/$eventKey');
    expect(link.dataset.params).toBe('{"eventKey":"2026miket"}');
  });
});

describe('EventLocationLink', () => {
  const mapsHref = `https://maps.google.com/?q=${encodeURIComponent(
    'Kettering University, 1700 University Ave, Flint, MI, USA',
  )}`;

  test('renders the venue and full location', () => {
    const { container } = render(<EventLocationLink event={event} />);
    expect(
      screen.getByRole('link', { name: 'Kettering University' }),
    ).toHaveProperty('href', mapsHref);
    expect(container.textContent).toBe(
      'Kettering University in Flint, MI, USA',
    );
  });

  test('hides USA next to the venue', () => {
    const { container } = render(<EventLocationLink event={event} hideUSA />);
    expect(container.textContent).toBe('Kettering University in Flint, MI');
  });

  test('keeps non-USA countries when hiding USA', () => {
    const { container } = render(
      <EventLocationLink
        event={{ ...event, country: 'Canada', state_prov: 'ON' }}
        hideUSA
      />,
    );
    expect(container.textContent).toBe(
      'Kettering University in Flint, ON, Canada',
    );
  });

  test('hides the venue', () => {
    render(<EventLocationLink event={event} hideVenue />);
    expect(screen.getByRole('link', { name: 'Flint, MI, USA' })).toHaveProperty(
      'href',
      mapsHref,
    );
  });

  test('hides the venue and USA', () => {
    render(<EventLocationLink event={event} hideVenue hideUSA />);
    expect(screen.getByRole('link', { name: 'Flint, MI' })).toBeTruthy();
  });

  test('hides the venue but keeps non-USA countries', () => {
    render(
      <EventLocationLink
        event={{ ...event, country: 'Canada', state_prov: 'ON' }}
        hideVenue
        hideUSA
      />,
    );
    expect(
      screen.getByRole('link', { name: 'Flint, ON, Canada' }),
    ).toBeTruthy();
  });
});

describe('TeamLocationLink', () => {
  test('abbreviates a known state and links to maps', () => {
    render(<TeamLocationLink team={team} />);
    const link = screen.getByRole('link', { name: 'San Jose, CA, USA' });
    expect(link).toHaveProperty(
      'href',
      `https://maps.google.com/?q=${encodeURIComponent('San Jose, California, USA')}`,
    );
  });

  test('hides USA', () => {
    render(<TeamLocationLink team={team} hideUSA />);
    expect(screen.getByRole('link', { name: 'San Jose, CA' })).toBeTruthy();
  });

  test('keeps unknown or missing provinces as-is', () => {
    render(
      <>
        <TeamLocationLink
          team={{ ...team, state_prov: 'Ontario', country: 'Canada' }}
          hideUSA
        />
        <TeamLocationLink team={{ ...team, state_prov: null }} />
      </>,
    );
    expect(
      screen.getByRole('link', { name: 'San Jose, Ontario, Canada' }),
    ).toBeTruthy();
    expect(screen.getByRole('link', { name: 'San Jose, , USA' })).toBeTruthy();
  });
});

describe('MatchLink', () => {
  const match = { key: '2026miket_qm1' } as Match;

  function renderWithClient(ui: ReactNode) {
    const queryClient = new QueryClient();
    render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
    );
    return queryClient;
  }

  test('opens the match modal and primes the cache on click', () => {
    const queryClient = renderWithClient(
      <MatchLink matchOrKey={match} event={event}>
        Q1
      </MatchLink>,
    );
    const link = screen.getByRole('link', { name: 'Q1' });
    expect(link.getAttribute('href')).toBe('.');
    expect(link.dataset.search).toBe(
      '{"tab":"results","matchKey":"2026miket_qm1"}',
    );
    expect(JSON.parse(link.dataset.mask ?? '')).toEqual({
      to: '/match/$matchKey',
      params: { matchKey: '2026miket_qm1' },
      unmaskOnReload: true,
    });
    expect(link.dataset.replace).toBe('true');
    expect(link.dataset.resetScroll).toBe('false');

    fireEvent.click(link);

    expect(
      queryClient.getQueryData(
        getMatchQueryKey({ path: { match_key: '2026miket_qm1' } }),
      ),
    ).toBe(match);
    expect(
      queryClient.getQueryData(
        getEventQueryKey({ path: { event_key: '2026miket' } }),
      ),
    ).toBe(event);
  });

  test('links directly to the match page without priming for a key', () => {
    const queryClient = renderWithClient(
      <MatchLink matchOrKey="2026miket_qm2" noModal>
        Q2
      </MatchLink>,
    );
    const link = screen.getByRole('link', { name: 'Q2' });
    expect(link.getAttribute('href')).toBe('/match/$matchKey');
    expect(link.dataset.params).toBe('{"matchKey":"2026miket_qm2"}');

    fireEvent.click(link);

    expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
  });
});

describe('DistrictLink', () => {
  test('links to a district with and without a year', () => {
    render(
      <>
        <DistrictLink districtAbbreviation="fim" year={2026}>
          FIM 2026
        </DistrictLink>
        <DistrictLink districtAbbreviation="fim">FIM</DistrictLink>
      </>,
    );
    const withYear = screen.getByRole('link', { name: 'FIM 2026' });
    expect(withYear.getAttribute('href')).toBe(
      '/district/$districtAbbreviation/{-$year}',
    );
    expect(withYear.dataset.params).toBe(
      '{"districtAbbreviation":"fim","year":"2026"}',
    );
    expect(screen.getByRole('link', { name: 'FIM' }).dataset.params).toBe(
      '{"districtAbbreviation":"fim"}',
    );
  });
});
