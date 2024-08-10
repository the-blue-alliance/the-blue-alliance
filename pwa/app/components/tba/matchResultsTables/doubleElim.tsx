import { groupBy } from 'lodash-es';
import { useMemo } from 'react';
import { Match } from '~/api/v3';
import MatchResultsTableBase from '~/components/tba/matchResultsTables/base';

const DOUBLE_ELIM_ROUND_MAPPING: { [key: number]: number } = {
  1: 1,
  2: 1,
  3: 1,
  4: 1,
  5: 2,
  6: 2,
  7: 2,
  8: 2,
  9: 3,
  10: 3,
  11: 4,
  12: 4,
  13: 5,
};

export default function MatchResultsTableDoubleElim({
  matches,
}: {
  matches: Match[];
}) {
  const nonFinals = useMemo(
    () => matches.filter((m) => m.comp_level !== 'f'),
    [matches],
  );

  const finals = useMemo(
    () => matches.filter((m) => m.comp_level === 'f'),
    [matches],
  );

  const matchesGroupedByRound = useMemo(
    () =>
      groupBy(nonFinals, (m) => DOUBLE_ELIM_ROUND_MAPPING[m.set_number] ?? 1),
    [nonFinals],
  );

  return (
    <>
      <h1 className="text-2xl font-bold">Playoff Results</h1>
      {Object.entries(matchesGroupedByRound).map(([round, matches]) => (
        <div key={round}>
          <div className="mt-1.5 text-lg">Round {round}</div>
          <MatchResultsTableBase
            matches={matches}
            matchTitleFormatter={(m) => `Match ${m.set_number}`}
          />
        </div>
      ))}

      {finals.length > 0 && (
        <>
          <div className="mt-1.5 text-lg">Finals</div>
          <MatchResultsTableBase
            matches={matches.filter((m) => m.comp_level === 'f')}
            matchTitleFormatter={(m) => `Final ${m.match_number}`}
          />
        </>
      )}
    </>
  );
}
