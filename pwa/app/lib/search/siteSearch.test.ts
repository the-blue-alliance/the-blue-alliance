import { describe, expect, test } from 'vitest';

import { SearchIndex } from '~/api/tba/read';
import { siteSearch } from '~/lib/search/siteSearch';

const SEASON = 2026;

describe('siteSearch', () => {
  test('returns nothing for a blank query', () => {
    const index: SearchIndex = {
      teams: [{ key: 'frc254', nickname: 'The Cheesy Poofs' }],
      events: [],
    };

    expect(siteSearch(index, '   ', SEASON)).toEqual([]);
  });

  test.each(['20', 'frc20', 'frc 20', 'team 20', 'Team 20'])(
    'ranks the exact team number match for %s first',
    (query) => {
      const index: SearchIndex = {
        teams: [
          { key: 'frc2056', nickname: 'OP Robotics' },
          { key: 'frc20', nickname: 'The Rocketeers' },
        ],
        events: [{ key: '2026grits', name: 'GRITS 20' }],
      };

      expect(siteSearch(index, query, SEASON)[0].key).toBe('frc20');
    },
  );

  test('matches team numbers by prefix rather than event years', () => {
    const index: SearchIndex = {
      teams: [
        { key: 'frc25', nickname: 'Raider Robotix' },
        { key: 'frc254', nickname: 'The Cheesy Poofs' },
      ],
      events: [{ key: '2025cc', name: 'Chezy Champs' }],
    };

    expect(siteSearch(index, '25', SEASON).map((r) => r.key)).toEqual([
      'frc25',
      'frc254',
    ]);
  });

  test('finds a team despite a typo in its nickname', () => {
    const index: SearchIndex = {
      teams: [{ key: 'frc254', nickname: 'The Cheesy Poofs' }],
      events: [],
    };

    expect(siteSearch(index, 'cheesey poofs', SEASON)[0].key).toBe('frc254');
  });

  test('ranks a team whose name matches exactly above an older event that only starts with the query', () => {
    const index: SearchIndex = {
      teams: [{ key: 'frc539', nickname: 'Titan Robotics' }],
      events: [{ key: '2021gamti', name: 'Titanium Group' }],
    };

    expect(siteSearch(index, 'titan', SEASON)[0].key).toBe('frc539');
  });

  test('ranks a current event above a team with the same name', () => {
    const index: SearchIndex = {
      teams: [{ key: 'frc9202', nickname: 'Silicon Valley Regional' }],
      events: [{ key: '2026casj', name: 'Silicon Valley Regional' }],
    };

    expect(siteSearch(index, 'Silicon Valley', SEASON)[0].key).toBe('2026casj');
  });

  test('lists every year of a recurring event, newest first', () => {
    const index: SearchIndex = {
      teams: [],
      events: [
        { key: '2024casj', name: 'Silicon Valley Regional' },
        { key: '2026casj', name: 'Silicon Valley Regional' },
        { key: '2025casj', name: 'Silicon Valley Regional' },
      ],
    };

    expect(
      siteSearch(index, 'silicon valley', SEASON).map((r) => r.key),
    ).toEqual(['2026casj', '2025casj', '2024casj']);
  });

  test('lists matching events newest first even when a longer name matched', () => {
    const index: SearchIndex = {
      teams: [],
      events: [
        { key: '2016cmp', name: 'Einstein Field' },
        { key: '2026cmptx', name: 'Einstein Field' },
        { key: '2019cmpmi', name: 'Einstein Field (Detroit)' },
      ],
    };

    expect(siteSearch(index, 'einstein', SEASON).map((r) => r.key)).toEqual([
      '2026cmptx',
      '2019cmpmi',
      '2016cmp',
    ]);
  });

  test('ranks the current season of a recurring event above a future one', () => {
    const index: SearchIndex = {
      teams: [],
      events: [
        { key: '2026hiho', name: 'Hawaii Regional' },
        { key: '2027hiho', name: 'Hawaii Regional' },
      ],
    };

    expect(siteSearch(index, 'hawaii', SEASON)[0].key).toBe('2026hiho');
  });

  test('shows a future event that has no earlier seasons', () => {
    const index: SearchIndex = {
      teams: [],
      events: [{ key: '2027wimuk', name: 'WIN District Mukwonago Event' }],
    };

    expect(siteSearch(index, 'mukwonago', SEASON)[0].key).toBe('2027wimuk');
  });

  test('matches an event by its own name rather than other years of the same event', () => {
    const index: SearchIndex = {
      teams: [],
      events: [
        { key: '2019cmptx', name: 'Einstein Field (Houston)' },
        { key: '2026cmptx', name: 'Einstein Field' },
      ],
    };

    expect(
      siteSearch(index, 'einstein houston', SEASON).map((r) => r.key),
    ).toEqual(['2019cmptx']);
  });

  test.each([
    ['year after the name', 'silicon valley 2024'],
    ['year before the code', '2024 casj'],
  ])('finds the event in the given year with the %s', (_, query) => {
    const index: SearchIndex = {
      teams: [],
      events: [
        { key: '2024casj', name: 'Silicon Valley Regional' },
        { key: '2026casj', name: 'Silicon Valley Regional' },
      ],
    };

    expect(siteSearch(index, query, SEASON).map((r) => r.key)).toEqual([
      '2024casj',
    ]);
  });

  test('links a team name with a year to the team year page', () => {
    const index: SearchIndex = {
      teams: [{ key: 'frc254', nickname: 'The Cheesy Poofs' }],
      events: [],
    };

    expect(siteSearch(index, 'cheesy poofs 2024', SEASON)[0].path).toBe(
      '/team/254/2024',
    );
  });

  test.each(['new', 'NEW', ' new '])(
    'ranks the exact event code match for %s above events whose names start with it',
    (query) => {
      const index: SearchIndex = {
        teams: [],
        events: [
          { key: '2026nyny', name: 'New York City Regional' },
          { key: '2026new', name: 'Newton Division' },
        ],
      };

      expect(siteSearch(index, query, SEASON)[0].key).toBe('2026new');
    },
  );

  test('ranks an exact event key match first', () => {
    const index: SearchIndex = {
      teams: [],
      events: [
        { key: '2026new', name: 'Newton Division' },
        { key: '2025new', name: 'Newton Division' },
      ],
    };

    expect(siteSearch(index, '2025new', SEASON)[0].key).toBe('2025new');
  });

  test('labels an event result with its year, trimmed name, and event code', () => {
    const index: SearchIndex = {
      teams: [],
      events: [{ key: '2026iri', name: 'Indiana Robotics Invitational ' }],
    };

    expect(siteSearch(index, '2026iri', SEASON)[0]).toEqual({
      type: 'event',
      key: '2026iri',
      label: '2026 Indiana Robotics Invitational [iri]',
      path: '/event/2026iri',
    });
  });

  test('returns at most 10 results', () => {
    const index: SearchIndex = {
      teams: Array.from({ length: 8 }, (_, i) => ({
        key: `frc${i + 1}`,
        nickname: `Robot Team ${i + 1}`,
      })),
      events: Array.from({ length: 8 }, (_, i) => ({
        key: `2026ev${i + 1}`,
        name: `Robot Event ${i + 1}`,
      })),
    };

    expect(siteSearch(index, 'Robot', SEASON)).toHaveLength(10);
  });

  test.each(['6324 2025', '6324/2025', 'frc6324 2025', ' 6324  /  2025 '])(
    'returns only the team year page for %s',
    (query) => {
      const index: SearchIndex = {
        teams: [
          { key: 'frc6324', nickname: 'The Blue Devils' },
          { key: 'frc2025', nickname: 'Silicon Valley Robotics' },
        ],
        events: [{ key: '2025cmptx', name: 'Einstein Field' }],
      };

      expect(siteSearch(index, query, SEASON)).toEqual([
        {
          type: 'team',
          key: 'frc6324',
          label: '6324 - The Blue Devils (2025)',
          path: '/team/6324/2025',
        },
      ]);
    },
  );

  test('falls back to a year-filtered search when the team in a team year query does not exist', () => {
    const index: SearchIndex = {
      teams: [{ key: 'frc254', nickname: 'The Cheesy Poofs' }],
      events: [
        { key: '2025week1', name: 'Week 1 2025' },
        { key: '2026week1', name: 'Week 1 2026' },
      ],
    };

    expect(siteSearch(index, '1 2026', SEASON).map((r) => r.path)).toEqual([
      '/event/2026week1',
    ]);
  });
});
