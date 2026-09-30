import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { PlayoffType } from '~/api/tba/read';
import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/event.$eventKey';

interface QueryOptions {
  queryKey: [{ _id: string; path: { event_key: string } }];
}

function fakeQueryClient(
  respond: (id: string, eventKey: string) => Promise<unknown>,
) {
  const ensureQueryData = vi.fn<(options: QueryOptions) => Promise<unknown>>(
    ({ queryKey }) => respond(queryKey[0]._id, queryKey[0].path.event_key),
  );
  return {
    queryClient: { ensureQueryData } as unknown as QueryClient,
    requested: () =>
      ensureQueryData.mock.calls.map(
        ([{ queryKey }]) => `${queryKey[0]._id}:${queryKey[0].path.event_key}`,
      ),
  };
}

function load(eventKey: string, queryClient: QueryClient) {
  return runLoader(Route, {
    params: { eventKey },
    context: { queryClient },
  });
}

const event = {
  key: '2024casj',
  name: 'Silicon Valley Regional',
  year: 2024,
  parent_event_key: null,
  division_keys: [],
  playoff_type: PlayoffType.DOUBLE_ELIM_8_TEAM,
};

describe('event route loader', () => {
  test('throws not-found for an invalid event key', async () => {
    const { queryClient } = fakeQueryClient(() => Promise.resolve([]));
    await expect(load('casj', queryClient)).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('throws not-found when the event fails to load', async () => {
    const { queryClient } = fakeQueryClient((id) =>
      id === 'getEvent'
        ? Promise.reject(new Error('404'))
        : Promise.resolve([]),
    );
    await expect(load('2024casj', queryClient)).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('tolerates failed match, alliance, and team fetches', async () => {
    const { queryClient } = fakeQueryClient((id) =>
      id === 'getEvent'
        ? Promise.resolve(event)
        : Promise.reject(new Error('500')),
    );
    await expect(load('2024casj', queryClient)).resolves.toEqual({
      eventKey: '2024casj',
      event,
    });
  });

  test('prefetches each division of a parent event', async () => {
    const { queryClient, requested } = fakeQueryClient((id) =>
      Promise.resolve(
        id === 'getEvent' ? { ...event, division_keys: ['2024cur'] } : [],
      ),
    );
    await load('2024cmptx', queryClient);
    expect(requested()).toContain('getEventSimple:2024cur');
  });

  test('prefetches sibling divisions through the parent event', async () => {
    const { queryClient, requested } = fakeQueryClient((id, eventKey) => {
      if (id !== 'getEvent') return Promise.resolve([]);
      return Promise.resolve(
        eventKey === '2024cur'
          ? { ...event, parent_event_key: '2024cmptx' }
          : { ...event, division_keys: ['2024cur', '2024gal'] },
      );
    });
    await load('2024cur', queryClient);
    await vi.waitFor(() =>
      expect(requested()).toContain('getEventSimple:2024gal'),
    );
  });

  test('does not prefetch the current division as its own sibling', async () => {
    const { queryClient, requested } = fakeQueryClient((id, eventKey) => {
      if (id !== 'getEvent') return Promise.resolve([]);
      return Promise.resolve(
        eventKey === '2024cur'
          ? { ...event, parent_event_key: '2024cmptx' }
          : { ...event, division_keys: ['2024cur', '2024gal'] },
      );
    });
    await load('2024cur', queryClient);
    await vi.waitFor(() =>
      expect(requested()).toContain('getEventSimple:2024gal'),
    );
    expect(requested()).not.toContain('getEventSimple:2024cur');
  });

  test('swallows a failed parent event fetch', async () => {
    const { queryClient } = fakeQueryClient((id, eventKey) => {
      if (id !== 'getEvent') return Promise.resolve([]);
      return eventKey === '2024cur'
        ? Promise.resolve({ ...event, parent_event_key: '2024cmptx' })
        : Promise.reject(new Error('500'));
    });
    await expect(load('2024cur', queryClient)).resolves.toMatchObject({
      eventKey: '2024cur',
    });
  });

  test('swallows a failed division fetch', async () => {
    const { queryClient } = fakeQueryClient((id) => {
      if (id === 'getEventSimple') return Promise.reject(new Error('500'));
      return Promise.resolve(
        id === 'getEvent' ? { ...event, division_keys: ['2024cur'] } : [],
      );
    });
    await expect(load('2024cmptx', queryClient)).resolves.toMatchObject({
      eventKey: '2024cmptx',
    });
  });

  test('swallows failed sibling division fetches', async () => {
    const { queryClient, requested } = fakeQueryClient((id, eventKey) => {
      if (id === 'getEventSimple') return Promise.reject(new Error('500'));
      if (id !== 'getEvent') return Promise.resolve([]);
      return Promise.resolve(
        eventKey === '2024cur'
          ? { ...event, parent_event_key: '2024cmptx' }
          : { ...event, division_keys: ['2024gal'] },
      );
    });
    await load('2024cur', queryClient);
    await vi.waitFor(() =>
      expect(requested()).toContain('getEventSimple:2024gal'),
    );
  });

  test('prefetches playoff advancement for round robin events', async () => {
    const { queryClient, requested } = fakeQueryClient((id) =>
      id === 'getEventPlayoffAdvancement'
        ? Promise.reject(new Error('500'))
        : Promise.resolve(
            id === 'getEvent'
              ? { ...event, playoff_type: PlayoffType.ROUND_ROBIN_6_TEAM }
              : [],
          ),
    );
    await load('2024casj', queryClient);
    expect(requested()).toContain('getEventPlayoffAdvancement:2024casj');
  });

  test('prefetches playoff advancement for average-score events', async () => {
    const { queryClient, requested } = fakeQueryClient((id) =>
      Promise.resolve(
        id === 'getEvent'
          ? { ...event, playoff_type: PlayoffType.AVG_SCORE_8_TEAM }
          : [],
      ),
    );
    await load('2015casj', queryClient);
    expect(requested()).toContain('getEventPlayoffAdvancement:2015casj');
  });

  test('skips playoff advancement for bracket events', async () => {
    const { queryClient, requested } = fakeQueryClient((id) =>
      Promise.resolve(id === 'getEvent' ? event : []),
    );
    await load('2024casj', queryClient);
    expect(requested()).not.toContain('getEventPlayoffAdvancement:2024casj');
  });
});

function jsonLd(loaderEvent: object) {
  const head = runHead(Route, {
    loaderData: { event: loaderEvent },
  });
  return JSON.parse(head?.scripts?.[0]?.children as string);
}

describe('event route head', () => {
  test('titles the page with the event name and year', () => {
    expect(runHead(Route, { loaderData: { event } })?.meta?.[0]).toEqual({
      title: 'Silicon Valley Regional (2024) - The Blue Alliance',
    });
  });

  test('falls back to a not-found title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Event Not Found - The Blue Alliance',
    });
  });

  test('describes the venue in structured data when coordinates exist', () => {
    expect(
      jsonLd({ ...event, lat: 37.3, lng: -121.9, location_name: 'SJSU' })
        .location.name,
    ).toBe('SJSU');
  });

  test('names the venue after the event when it has no location name', () => {
    expect(
      jsonLd({ ...event, lat: 37.3, lng: -121.9, location_name: null }).location
        .name,
    ).toBe('Silicon Valley Regional');
  });

  test('omits the venue from structured data without coordinates', () => {
    expect(jsonLd({ ...event, lat: null, lng: null }).location).toBeUndefined();
  });
});
