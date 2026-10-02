import type { QueryClient } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';

import { PlayoffType } from '~/api/tba/read';
import { runHead, runLoader } from '~/routes/-testUtils';
import { Route } from '~/routes/match.$matchKey';

function load(matchKey: string, match: Promise<unknown>) {
  const queryClient = {
    ensureQueryData: vi.fn<
      (options: { queryKey: [{ _id: string }] }) => Promise<unknown>
    >(({ queryKey }) =>
      queryKey[0]._id === 'getMatch' ? match : Promise.resolve(event),
    ),
  } as unknown as QueryClient;
  return runLoader(Route, {
    params: { matchKey },
    context: { queryClient },
  });
}

const event = {
  key: '2024casj',
  name: 'Silicon Valley Regional',
  year: 2024,
  city: 'San Jose',
  state_prov: 'CA',
  country: 'USA',
  location_name: 'SJSU',
  playoff_type: PlayoffType.DOUBLE_ELIM_8_TEAM,
};

const match = {
  key: '2024casj_qm1',
  comp_level: 'qm',
  set_number: 1,
  match_number: 1,
  actual_time: null,
  videos: [],
  alliances: {
    red: { team_keys: ['frc254'] },
    blue: { team_keys: ['frc604'] },
  },
};

function head(loaderData: object) {
  return runHead(Route, { loaderData });
}

function jsonLd(overrides: { event?: object; match?: object }) {
  const result = head({
    event: { ...event, ...overrides.event },
    match: { ...match, ...overrides.match },
  });
  return JSON.parse(result?.scripts?.[0]?.children as string);
}

describe('match route loader', () => {
  test('loads the match and its event', async () => {
    await expect(load('2024casj_qm1', Promise.resolve(match))).resolves.toEqual(
      {
        eventKey: '2024casj',
        matchKey: '2024casj_qm1',
        event,
        match,
      },
    );
  });

  test('throws not-found for an invalid match key', async () => {
    await expect(
      load('2024casj', Promise.resolve(match)),
    ).rejects.toMatchObject({ isNotFound: true });
  });

  test('throws not-found when the match fails to load', async () => {
    await expect(
      load('2024casj_qm1', Promise.reject(new Error('404'))),
    ).rejects.toMatchObject({ isNotFound: true });
  });
});

describe('match route head', () => {
  test('titles the page with the match and event', () => {
    expect(head({ event, match })?.meta?.[0]).toEqual({
      title: 'Quals 1 - Silicon Valley Regional (2024) - The Blue Alliance',
    });
  });

  test('falls back to a generic title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Match Information - The Blue Alliance',
    });
  });

  test('uses the custom playoff format when the event has none', () => {
    expect(
      head({
        event: { ...event, playoff_type: null },
        match: { ...match, comp_level: 'sf', set_number: 2 },
      })?.meta?.[0],
    ).toEqual({
      title:
        'Semis 2 Match 1 - Silicon Valley Regional (2024) - The Blue Alliance',
    });
  });

  test('includes the start time once the match is played', () => {
    expect(jsonLd({ match: { actual_time: 1700000000 } }).startDate).toBe(
      '2023-11-14T22:13:20Z',
    );
  });

  test('names the venue after the event when it has no location name', () => {
    expect(jsonLd({ event: { location_name: null } }).location.name).toBe(
      'Silicon Valley Regional',
    );
  });

  test('links a single YouTube video directly', () => {
    expect(
      jsonLd({
        match: {
          videos: [
            { type: 'youtube', key: 'abc' },
            { type: 'tba', key: 'x' },
          ],
        },
      }).subjectOf.url,
    ).toBe('https://www.youtube.com/watch?v=abc');
  });

  test('lists multiple YouTube videos', () => {
    expect(
      jsonLd({
        match: {
          videos: [
            { type: 'youtube', key: 'abc' },
            { type: 'youtube', key: 'def' },
          ],
        },
      }).subjectOf,
    ).toHaveLength(2);
  });

  test('lists each alliance team as a competitor', () => {
    expect(jsonLd({}).competitor[1].member).toEqual([
      {
        '@type': 'SportsTeam',
        name: 'Team 604',
        url: 'https://www.thebluealliance.com/team/604',
      },
    ]);
  });
});
