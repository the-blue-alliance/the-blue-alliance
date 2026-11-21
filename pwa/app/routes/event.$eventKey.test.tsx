import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { PlayoffType } from '~/api/tba/read';
import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/event.$eventKey';

interface QueryOptions {
  queryKey: [{ _id: string; path: { event_key?: string; year?: number } }];
}

function fakeQueryClient(
  respond: (id: string, eventKey: string | undefined) => Promise<unknown>,
) {
  const ensureQueryData = vi.fn<(options: QueryOptions) => Promise<unknown>>(
    ({ queryKey }) => respond(queryKey[0]._id, queryKey[0].path.event_key),
  );
  const prefetchQuery = vi.fn<() => Promise<void>>(() => Promise.resolve());
  return { ensureQueryData, prefetchQuery } as unknown as QueryClient;
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
    const queryClient = fakeQueryClient(() => Promise.resolve([]));
    await expect(load('casj', queryClient)).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('throws not-found when the event fails to load', async () => {
    const queryClient = fakeQueryClient((id) =>
      id === 'getEvent'
        ? Promise.reject(new Error('404'))
        : Promise.resolve([]),
    );
    await expect(load('2024casj', queryClient)).rejects.toMatchObject({
      isNotFound: true,
    });
  });

  test('tolerates failed match and alliance fetches', async () => {
    const queryClient = fakeQueryClient((id) =>
      id === 'getEvent'
        ? Promise.resolve(event)
        : Promise.reject(new Error('500')),
    );
    await expect(load('2024casj', queryClient)).resolves.toEqual({
      eventKey: '2024casj',
      event,
    });
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
