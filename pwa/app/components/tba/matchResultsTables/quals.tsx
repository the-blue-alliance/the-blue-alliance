import { Match } from '~/api/v3';
import MatchResultsTableBase from '~/components/tba/matchResultsTables/base';

export default function MatchResultsTableQuals({
  matches,
}: {
  matches: Match[];
}) {
  return (
    <>
      <div className="text-2xl">Qualification Results</div>
      <MatchResultsTableBase
        matches={matches}
        matchTitleFormatter={(m) => `Qual ${m.match_number}`}
      />
    </>
  );
}
