import { describe, expect, test } from 'vitest';

import { PlayoffType } from '~/api/tba/read';
import {
  DOUBLE_ELIM_ROUND_MAPPING,
  ROUND_ROBIN_TYPES,
  TRADITIONAL_BRACKET_TYPES,
} from '~/lib/api/PlayoffType';

describe('TRADITIONAL_BRACKET_TYPES', () => {
  test('treats legacy events without a playoff type as a bracket', () => {
    expect(TRADITIONAL_BRACKET_TYPES.has(null)).toBe(true);
  });

  test('does not include double elimination', () => {
    expect(TRADITIONAL_BRACKET_TYPES.has(PlayoffType.DOUBLE_ELIM_8_TEAM)).toBe(
      false,
    );
  });
});

describe('ROUND_ROBIN_TYPES', () => {
  test('is only the six alliance round robin', () => {
    expect([...ROUND_ROBIN_TYPES]).toEqual([PlayoffType.ROUND_ROBIN_6_TEAM]);
  });
});

describe('DOUBLE_ELIM_ROUND_MAPPING', () => {
  test('covers all 13 double elimination matches', () => {
    expect(DOUBLE_ELIM_ROUND_MAPPING.size).toBe(13);
  });

  test('places match 13 in the fifth round', () => {
    expect(DOUBLE_ELIM_ROUND_MAPPING.get(13)).toBe(5);
  });
});
