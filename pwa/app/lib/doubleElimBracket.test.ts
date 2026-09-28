import { describe, expect, test } from 'vitest';

import { type Match } from '~/api/tba/read';
import {
  DOUBLE_ELIM_4_SLOTS,
  DOUBLE_ELIM_8_SLOTS,
  nextSeriesLabel,
  resolveBracketSides,
  seriesOutcome,
} from '~/lib/doubleElimBracket';

describe('resolveBracketSides', () => {
  test('seeds round one from alliance numbers before any match is played', () => {
    const sides = resolveBracketSides(DOUBLE_ELIM_8_SLOTS, {});

    expect(sides['Match 2']).toEqual({
      red: { allianceNumber: 4 },
      blue: { allianceNumber: 5 },
    });
  });

  test.each([
    { name: 'winner to upper bracket', label: 'Match 7', expected: 1 },
    { name: 'loser to lower bracket', label: 'Match 5', expected: 8 },
  ])('sends match 1 $name', ({ label, expected }) => {
    const sides = resolveBracketSides(DOUBLE_ELIM_8_SLOTS, {
      'Match 1': { winner: 1, loser: 8 },
    });

    expect(sides[label].red).toEqual({ allianceNumber: expected });
  });

  test('shows a loser placeholder for match 13 before match 11 is played', () => {
    const sides = resolveBracketSides(DOUBLE_ELIM_8_SLOTS, {});

    expect(sides['Match 13'].red).toEqual({ placeholder: 'Loser of Match 11' });
  });

  test('places the match 6 winner on the blue side of match 9', () => {
    const sides = resolveBracketSides(DOUBLE_ELIM_8_SLOTS, {
      'Match 6': { winner: 6, loser: 7 },
    });

    expect(sides['Match 9'].blue).toEqual({ allianceNumber: 6 });
  });

  test('shows a winner placeholder for the 4 alliance finals blue side', () => {
    const sides = resolveBracketSides(DOUBLE_ELIM_4_SLOTS, {});

    expect(sides.Finals.blue).toEqual({ placeholder: 'Winner of Match 5' });
  });
});

describe('seriesOutcome', () => {
  test('returns blue as winner when blue won', () => {
    expect(
      seriesOutcome({
        redAllianceNumber: 1,
        blueAllianceNumber: 8,
        redWon: false,
        blueWon: true,
      }),
    ).toEqual({ winner: 8, loser: 1 });
  });

  test('returns no outcome for an unplayed series', () => {
    expect(
      seriesOutcome({
        redAllianceNumber: 1,
        blueAllianceNumber: 8,
        redWon: false,
        blueWon: false,
      }),
    ).toBeUndefined();
  });
});

describe('nextSeriesLabel', () => {
  const played = {
    alliances: { red: { score: 100 }, blue: { score: 50 } },
  } as unknown as Match;
  const unplayed = {
    alliances: { red: { score: -1 }, blue: { score: -1 } },
  } as unknown as Match;

  test('picks the first match before any match is played', () => {
    expect(
      nextSeriesLabel({ 'Match 1': undefined, 'Match 2': undefined }),
    ).toBe('Match 1');
  });

  test('skips a match with a posted score', () => {
    expect(
      nextSeriesLabel({ 'Match 1': [played], 'Match 2': [unplayed] }),
    ).toBe('Match 2');
  });

  test('returns nothing once any finals match has a posted score', () => {
    expect(
      nextSeriesLabel({ 'Match 5': [played], Finals: [played, unplayed] }),
    ).toBeUndefined();
  });
});
