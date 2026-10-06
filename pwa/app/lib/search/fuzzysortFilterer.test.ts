import { Temporal } from 'temporal-polyfill';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import { SearchIndex } from '~/api/tba/read';
import FuzzysortFilterer from '~/lib/search/fuzzysortFilterer';

const SEARCH_INDEX: SearchIndex = {
  teams: [
    { key: 'frc254', nickname: 'The Cheesy Poofs' },
    { key: 'frc6324', nickname: 'The Blue Devils' },
    { key: 'frc2025', nickname: 'Silicon Valley Robotics' },
  ],
  events: [
    { key: '2026casj', name: 'Silicon Valley Regional' },
    { key: '2025cmptx', name: 'Einstein Field' },
  ],
};

describe('FuzzysortFilterer', () => {
  beforeEach(() => {
    vi.spyOn(Temporal.Now, 'plainDateISO').mockReturnValue(
      Temporal.PlainDate.from('2026-10-02'),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('ranks teams and events together in one list by score', () => {
    const results = new FuzzysortFilterer().filter(
      SEARCH_INDEX,
      'Silicon Valley',
    );

    expect(results.map((r) => r.key)).toEqual(['2026casj', 'frc2025']);
  });

  test.each(['20', 'frc20'])(
    'ranks the exact team number match for %s above current events',
    (query) => {
      const index: SearchIndex = {
        teams: [{ key: 'frc20', nickname: 'The Rocketeers' }],
        events: [{ key: '2026grits', name: 'GRITS 2026' }],
      };

      expect(new FuzzysortFilterer().filter(index, query)[0].key).toBe('frc20');
    },
  );

  test('labels an event result with its year, name, and event code', () => {
    const [result] = new FuzzysortFilterer().filter(SEARCH_INDEX, '2026casj');

    expect(result).toEqual({
      type: 'event',
      key: '2026casj',
      label: '2026 Silicon Valley Regional [casj]',
      path: '/event/2026casj',
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

    expect(new FuzzysortFilterer().filter(index, 'Robot')).toHaveLength(10);
  });

  test.each(['6324 2025', '6324/2025', 'frc6324 2025', ' 6324  /  2025 '])(
    'returns only the team year page for %s',
    (query) => {
      expect(new FuzzysortFilterer().filter(SEARCH_INDEX, query)).toEqual([
        {
          type: 'team',
          key: 'frc6324',
          label: '6324 - The Blue Devils (2025)',
          path: '/team/6324/2025',
        },
      ]);
    },
  );

  test('falls back to fuzzy search when the team in a team year query does not exist', () => {
    const index: SearchIndex = {
      teams: [{ key: 'frc254', nickname: 'The Cheesy Poofs' }],
      events: [{ key: '2026week1', name: 'Week 1 2026' }],
    };

    const results = new FuzzysortFilterer().filter(index, '1 2026');

    expect(results.map((r) => r.path)).toEqual(['/event/2026week1']);
  });
});
