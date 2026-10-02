import { type Match } from '~/api/tba/read';
import { matchHasBeenPlayed } from '~/lib/matchUtils';

export type SlotSource =
  { seed: number } | { winnerOf: string } | { loserOf: string };

export interface BracketSlot {
  red: SlotSource;
  blue: SlotSource;
}

export interface SeriesOutcome {
  winner: number | null;
  loser: number | null;
}

export type BracketSide = { allianceNumber: number } | { placeholder: string };

export interface BracketSides {
  red: BracketSide;
  blue: BracketSide;
}

export const DOUBLE_ELIM_8_SLOTS: Record<string, BracketSlot> = {
  'Match 1': { red: { seed: 1 }, blue: { seed: 8 } },
  'Match 2': { red: { seed: 4 }, blue: { seed: 5 } },
  'Match 3': { red: { seed: 2 }, blue: { seed: 7 } },
  'Match 4': { red: { seed: 3 }, blue: { seed: 6 } },
  'Match 5': { red: { loserOf: 'Match 1' }, blue: { loserOf: 'Match 2' } },
  'Match 6': { red: { loserOf: 'Match 3' }, blue: { loserOf: 'Match 4' } },
  'Match 7': { red: { winnerOf: 'Match 1' }, blue: { winnerOf: 'Match 2' } },
  'Match 8': { red: { winnerOf: 'Match 3' }, blue: { winnerOf: 'Match 4' } },
  'Match 9': { red: { loserOf: 'Match 7' }, blue: { winnerOf: 'Match 6' } },
  'Match 10': { red: { loserOf: 'Match 8' }, blue: { winnerOf: 'Match 5' } },
  'Match 11': { red: { winnerOf: 'Match 7' }, blue: { winnerOf: 'Match 8' } },
  'Match 12': { red: { winnerOf: 'Match 10' }, blue: { winnerOf: 'Match 9' } },
  'Match 13': { red: { loserOf: 'Match 11' }, blue: { winnerOf: 'Match 12' } },
  Finals: { red: { winnerOf: 'Match 11' }, blue: { winnerOf: 'Match 13' } },
};

export const DOUBLE_ELIM_4_SLOTS: Record<string, BracketSlot> = {
  'Match 1': { red: { seed: 1 }, blue: { seed: 4 } },
  'Match 2': { red: { seed: 2 }, blue: { seed: 3 } },
  'Match 3': { red: { winnerOf: 'Match 1' }, blue: { winnerOf: 'Match 2' } },
  'Match 4': { red: { loserOf: 'Match 1' }, blue: { loserOf: 'Match 2' } },
  'Match 5': { red: { loserOf: 'Match 3' }, blue: { winnerOf: 'Match 4' } },
  Finals: { red: { winnerOf: 'Match 3' }, blue: { winnerOf: 'Match 5' } },
};

function resolveSide(
  source: SlotSource,
  outcomes: Record<string, SeriesOutcome | undefined>,
): BracketSide {
  if ('seed' in source) {
    return { allianceNumber: source.seed };
  }
  if ('winnerOf' in source) {
    const winner = outcomes[source.winnerOf]?.winner;
    return winner
      ? { allianceNumber: winner }
      : { placeholder: `Winner of ${source.winnerOf}` };
  }
  const loser = outcomes[source.loserOf]?.loser;
  return loser
    ? { allianceNumber: loser }
    : { placeholder: `Loser of ${source.loserOf}` };
}

export function resolveBracketSides(
  slots: Record<string, BracketSlot>,
  outcomes: Record<string, SeriesOutcome | undefined>,
): Record<string, BracketSides> {
  return Object.fromEntries(
    Object.entries(slots).map(([label, slot]) => [
      label,
      {
        red: resolveSide(slot.red, outcomes),
        blue: resolveSide(slot.blue, outcomes),
      },
    ]),
  );
}

export function seriesOutcome(
  result: {
    redAllianceNumber: number | null;
    blueAllianceNumber: number | null;
    redWon: boolean;
    blueWon: boolean;
  } | null,
): SeriesOutcome | undefined {
  if (result?.redWon) {
    return {
      winner: result.redAllianceNumber,
      loser: result.blueAllianceNumber,
    };
  }
  if (result?.blueWon) {
    return {
      winner: result.blueAllianceNumber,
      loser: result.redAllianceNumber,
    };
  }
  return undefined;
}

export function sideAllianceNumber(side: BracketSide): number | null {
  return 'allianceNumber' in side ? side.allianceNumber : null;
}

export function nextSeriesLabel(
  matchLookup: Record<string, Match[] | undefined>,
): string | undefined {
  return Object.keys(matchLookup).find(
    (label) => !matchLookup[label]?.some(matchHasBeenPlayed),
  );
}
