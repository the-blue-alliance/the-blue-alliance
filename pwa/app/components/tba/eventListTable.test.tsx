// @vitest-environment jsdom
import { cleanup, render, screen, within } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import { Event, EventType } from '~/api/tba/read';
import EventListTable from '~/components/tba/eventListTable';

const { isEventActiveMock, isEventOnlineMock } = vi.hoisted(() => ({
  isEventActiveMock: vi.fn<(event: Event) => boolean>(),
  isEventOnlineMock: vi.fn<(event: Event) => boolean>(),
}));

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    params,
    to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children: ReactNode;
    params: { eventKey: string };
    to: string;
  }) => (
    <a href={to.replace('$eventKey', params.eventKey)} {...props}>
      {children}
    </a>
  ),
}));

vi.mock('~/lib/eventUtils', async (importOriginal) => {
  const actual = await importOriginal<typeof import('~/lib/eventUtils')>();
  return { ...actual, isEventActive: isEventActiveMock };
});

vi.mock('~/lib/gameday/useOnlineEventWebcasts', () => ({
  useOnlineEventWebcasts: () => isEventOnlineMock,
}));

function makeEvent(overrides: Partial<Event> = {}): Event {
  return {
    key: '2026miket',
    name: 'Kettering University Event #1',
    event_code: 'miket',
    event_type: EventType.DISTRICT,
    district: null,
    city: 'Flint',
    state_prov: 'MI',
    country: 'USA',
    start_date: '2026-03-01',
    end_date: '2026-03-03',
    year: 2026,
    short_name: 'Kettering #1',
    event_type_string: 'District',
    week: 0,
    address: null,
    postal_code: null,
    gmaps_place_id: null,
    gmaps_url: null,
    lat: null,
    lng: null,
    location_name: null,
    timezone: 'America/Detroit',
    website: null,
    first_event_id: null,
    first_event_code: null,
    webcasts: [],
    division_keys: [],
    parent_event_key: null,
    playoff_type: null,
    playoff_type_string: null,
    remap_teams: null,
    ...overrides,
  };
}

function district(abbreviation: string): NonNullable<Event['district']> {
  return {
    abbreviation,
    display_name: 'FIRST in Michigan',
    key: `2026${abbreviation.toLowerCase()}`,
    year: 2026,
    official_advancement_counts: { dcmp: 160, cmp: 82 },
  };
}

function rowForEvent(name: string): HTMLTableRowElement {
  const row = screen.getByRole('link', { name }).closest('tr');
  if (!(row instanceof HTMLTableRowElement)) {
    throw new Error(`Could not find the table row for ${name}`);
  }
  return row;
}

describe('EventListTable', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    isEventActiveMock.mockReturnValue(false);
    isEventOnlineMock.mockReturnValue(false);
  });

  afterEach(() => {
    cleanup();
  });

  test('renders the table headers', () => {
    render(<EventListTable events={[]} />);

    expect(
      screen.getAllByRole('columnheader').map((cell) => cell.textContent),
    ).toEqual(['Event', 'Webcast', 'Dates']);
  });

  test('links to an event and shows its location', () => {
    render(<EventListTable events={[makeEvent()]} />);

    const link = screen.getByRole('link', {
      name: 'Kettering University Event #1',
    });
    expect({
      href: link.getAttribute('href'),
      location: screen.getByText('Flint, MI, USA').textContent,
    }).toEqual({
      href: '/event/2026miket',
      location: 'Flint, MI, USA',
    });
  });

  test('shows the event date range', () => {
    render(<EventListTable events={[makeEvent()]} />);

    expect(screen.getByText('Mar 1 to Mar 3, 2026').textContent).toBe(
      'Mar 1 to Mar 3, 2026',
    );
  });

  test('groups divisions after their parent and trims parent name prefixes', () => {
    const parent = makeEvent({
      key: '2026necmp',
      name: 'New England District Championship',
      division_keys: ['2026necmp2', '2026necmp1'],
    });
    const firstDivision = makeEvent({
      key: '2026necmp1',
      name: 'New England District Championship - Ganson Division',
      parent_event_key: parent.key,
    });
    const secondDivision = makeEvent({
      key: '2026necmp2',
      name: 'New England District Championship - Richardson Division',
      parent_event_key: parent.key,
    });

    render(<EventListTable events={[secondDivision, parent, firstDivision]} />);

    expect(screen.getAllByRole('link').map((link) => link.textContent)).toEqual(
      [
        'New England District Championship',
        'Ganson Division',
        'Richardson Division',
      ],
    );
  });

  test('omits location details from division rows', () => {
    const parent = makeEvent({
      key: '2026necmp',
      name: 'New England District Championship',
      city: 'Springfield',
      state_prov: 'MA',
      division_keys: ['2026necmp1'],
    });
    const division = makeEvent({
      key: '2026necmp1',
      name: 'New England District Championship - Ganson Division',
      city: 'Division City',
      parent_event_key: parent.key,
    });

    render(<EventListTable events={[parent, division]} />);

    expect(
      within(rowForEvent('Ganson Division')).queryByText(/Division City/),
    ).toBeNull();
  });

  test.each([
    ['FIM', 'border-l-district-fim'],
    ['in', 'border-l-district-fin'],
    ['mar', 'border-l-district-fma'],
    ['tx', 'border-l-district-fit'],
  ])('applies the district color for %s', (abbreviation, colorClass) => {
    render(
      <EventListTable
        events={[makeEvent({ district: district(abbreviation) })]}
      />,
    );

    expect(
      rowForEvent('Kettering University Event #1').className.split(' '),
    ).toEqual(expect.arrayContaining(['border-l-4', colorClass]));
  });

  test('styles division rows and carries their district color inside the row', () => {
    const parent = makeEvent({
      key: '2026necmp',
      name: 'New England District Championship',
      district: district('ne'),
      division_keys: ['2026necmp1'],
    });
    const division = makeEvent({
      key: '2026necmp1',
      name: 'New England District Championship - Ganson Division',
      district: district('ne'),
      parent_event_key: parent.key,
    });

    render(<EventListTable events={[parent, division]} />);

    const row = rowForEvent('Ganson Division');
    const firstCell = row.cells.item(0);
    const districtMarker = Array.from(firstCell?.children ?? []).find((child) =>
      child.className.includes('border-l-district-ne'),
    );
    expect({
      rowClasses: row.className,
      cellClasses: firstCell?.className,
      hasDistrictMarker: districtMarker !== undefined,
    }).toEqual({
      rowClasses: expect.stringContaining('bg-muted/40'),
      cellClasses: expect.stringContaining('pl-[26px]'),
      hasDistrictMarker: true,
    });
  });

  test('adds a separator only between sibling division rows', () => {
    const parent = makeEvent({
      key: '2026necmp',
      name: 'New England District Championship',
      division_keys: ['2026necmp1', '2026necmp2'],
    });
    const firstDivision = makeEvent({
      key: '2026necmp1',
      name: 'New England District Championship - Ganson Division',
    });
    const secondDivision = makeEvent({
      key: '2026necmp2',
      name: 'New England District Championship - Richardson Division',
    });

    render(<EventListTable events={[parent, firstDivision, secondDivision]} />);

    expect({
      first:
        rowForEvent('Ganson Division').className.includes('border-b-border/40'),
      last: rowForEvent('Richardson Division').className.includes(
        'border-b-border/40',
      ),
    }).toEqual({ first: true, last: false });
  });

  test('does not show a webcast control when no webcasts are configured', () => {
    render(<EventListTable events={[makeEvent()]} />);

    expect(screen.queryByText(/Watch Now|Offline/)).toBeNull();
  });

  test('disables the webcast control when an event is offline and inactive', () => {
    render(
      <EventListTable
        events={[
          makeEvent({ webcasts: [{ type: 'youtube', channel: 'tba' }] }),
        ]}
      />,
    );

    const button = screen.getByRole('button', { name: 'Offline' });
    expect({
      disabled: (button as HTMLButtonElement).disabled,
      hasGamedayLink: screen.queryByRole('link', { name: 'Offline' }) !== null,
    }).toEqual({ disabled: true, hasGamedayLink: false });
  });

  test('links to gameday when an offline event is active', () => {
    isEventActiveMock.mockReturnValue(true);
    render(
      <EventListTable
        events={[
          makeEvent({ webcasts: [{ type: 'youtube', channel: 'tba' }] }),
        ]}
      />,
    );

    const link = screen.getByRole('link', { name: 'Offline' });
    expect({
      href: link.getAttribute('href'),
      target: link.getAttribute('target'),
      variantClass: link.className.includes('bg-secondary'),
    }).toEqual({
      href: '/gameday/2026miket',
      target: '_blank',
      variantClass: true,
    });
  });

  test('shows a success gameday link when an event is online', () => {
    isEventOnlineMock.mockReturnValue(true);
    render(
      <EventListTable
        events={[
          makeEvent({ webcasts: [{ type: 'youtube', channel: 'tba' }] }),
        ]}
      />,
    );

    const link = screen.getByRole('link', { name: 'Watch Now' });
    expect({
      href: link.getAttribute('href'),
      variantClass: link.className.includes('bg-green-600'),
    }).toEqual({ href: '/gameday/2026miket', variantClass: true });
  });
});
