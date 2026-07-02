import { describe, expect, it } from 'vitest';

import { firstSearchResult, keyToPath } from '~/lib/search/fuzzysortFilterer';

const team = (key: string) => ({ key, nickname: '' });
const event = (key: string) => ({ key, name: '' });

describe('keyToPath', () => {
  it('maps a team key to its team route', () => {
    expect(keyToPath('frc254')).toBe('/team/254');
    expect(keyToPath('frc10221')).toBe('/team/10221');
  });

  it('maps an event key to its event route', () => {
    expect(keyToPath('2024casj')).toBe('/event/2024casj');
  });
});

describe('firstSearchResult', () => {
  it('returns the top team when teamsFirst is set', () => {
    expect(
      firstSearchResult({
        teams: [team('frc1022'), team('frc10221')],
        events: [event('2024casj')],
        teamsFirst: true,
      }),
    ).toEqual({ type: 'team', value: 'frc1022', path: '/team/1022' });
  });

  it('returns the top event when not teamsFirst, even if a team also matches', () => {
    // cmdk shows the higher-scoring group first; Enter must follow that, not
    // unconditionally prefer a team the way the /search-route helper does.
    expect(
      firstSearchResult({
        teams: [team('frc254')],
        events: [event('2024casj')],
        teamsFirst: false,
      }),
    ).toEqual({ type: 'event', value: '2024casj', path: '/event/2024casj' });
  });

  it('falls back to the other group when the preferred group is empty', () => {
    expect(
      firstSearchResult({
        teams: [],
        events: [event('2024casj')],
        teamsFirst: true,
      }),
    ).toEqual({ type: 'event', value: '2024casj', path: '/event/2024casj' });

    expect(
      firstSearchResult({
        teams: [team('frc254')],
        events: [],
        teamsFirst: false,
      }),
    ).toEqual({ type: 'team', value: 'frc254', path: '/team/254' });
  });

  it('returns null when there are no results', () => {
    expect(
      firstSearchResult({ teams: [], events: [], teamsFirst: true }),
    ).toBeNull();
  });
});
