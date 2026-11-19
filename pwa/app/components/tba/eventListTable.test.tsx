import { render, screen, within } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { Event, EventType } from '~/api/tba/read';
import EventListTable from '~/components/tba/eventListTable';
import { makeEvent as baseEvent } from '~/test/factories';

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
  return baseEvent({
    key: '2026miket',
    name: 'Kettering University Event #1',
    event_code: 'miket',
    event_type: EventType.DISTRICT,
    city: 'Flint',
    state_prov: 'MI',
    country: 'USA',
    short_name: 'Kettering #1',
    event_type_string: 'District',
    timezone: 'America/Detroit',
    ...overrides,
  });
}

describe('EventListTable', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    isEventActiveMock.mockReturnValue(false);
    isEventOnlineMock.mockReturnValue(false);
  });

  test('renders the table headers', () => {
    render(<EventListTable events={[]} />);

    expect(
      screen.getAllByRole('columnheader').map((cell) => cell.textContent),
    ).toEqual(['Event', 'Webcast']);
  });

  test('links to an event', () => {
    render(<EventListTable events={[makeEvent()]} />);

    expect(
      screen
        .getByRole('link', { name: 'Kettering University Event #1' })
        .getAttribute('href'),
    ).toBe('/event/2026miket');
  });

  test('shows the location and date range on one line', () => {
    render(<EventListTable events={[makeEvent()]} />);

    expect(screen.getByText(/^Flint, MI, USA/).textContent).toBe(
      'Flint, MI, USA · Mar 1–3',
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
      within(screen.getByRole('row', { name: /Ganson Division/ })).queryByText(
        /Division City/,
      ),
    ).toBeNull();
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
    }).toEqual({
      href: '/gameday/2026miket',
      target: '_blank',
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
    expect(link.getAttribute('href')).toBe('/gameday/2026miket');
  });
});
