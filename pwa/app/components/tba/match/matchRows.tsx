import { Link } from 'react-router';

import PlayCircle from '~icons/bi/play-circle';

import { Event, Match } from '~/api/tba/read';
import { ShouldInsertBreakCallback } from '~/components/tba/match/breakers';
import ScoreCell from '~/components/tba/match/scoreCell';
import TeamListSubgrid from '~/components/tba/match/teamListSubgrid';
import { PlayoffType } from '~/lib/api/PlayoffType';
import { matchTitleShort, maybeGetFirstMatchVideoURL } from '~/lib/matchUtils';
import { cn } from '~/lib/utils';

export default function SimpleMatchRowsWithBreaks({
  matches,
  event,
  breakers,
}: {
  matches: Match[];
  event: Event;
  breakers: ShouldInsertBreakCallback[];
}) {
  const divs = [];

  for (let i = 0; i < matches.length; i++) {
    const match = matches[i];
    const maybeNextMatch = i < matches.length - 1 ? matches[i + 1] : null;

    for (const breaker of breakers) {
      const result = breaker({
        match,
        matchIndex: i,
        nextMatch: maybeNextMatch,
        event,
      });

      if (result.shouldBreak && result.whereToInsertBreak === 'before') {
        divs.push(
          <BreakRow key={`break-${i}`} text={result.text ?? 'Break'} />,
        );
      }
    }

    divs.push(
      <MatchRow
        match={match}
        playoffType={event.playoff_type ?? PlayoffType.CUSTOM}
        key={match.key}
      />,
    );

    for (const breaker of breakers) {
      const result = breaker({
        match,
        matchIndex: i,
        nextMatch: maybeNextMatch,
        event,
      });

      if (result.shouldBreak && result.whereToInsertBreak === 'after') {
        divs.push(
          <BreakRow key={`break-${i}`} text={result.text ?? 'Break'} />,
        );
      }
    }
  }

  return <div className="flex flex-col gap-y-1">{divs}</div>;
}

export function MatchRow({
  match,
  playoffType,
}: {
  match: Match;
  playoffType: PlayoffType;
}) {
  const maybeVideoURL = maybeGetFirstMatchVideoURL(match);
  const isPlayed =
    match.alliances.red.score !== -1 && match.alliances.blue.score !== -1;

  return (
    <div>
      {/* Desktop: 1x11 grid, Mobile: 2x6 grid */}
      <div
        className="mx-auto grid w-full max-w-6xl
          grid-cols-[auto_6em_repeat(4,1fr)] grid-rows-[2.5em_2.5em] gap-x-1
          text-sm xl:grid-cols-[auto_6em_repeat(9,1fr)] xl:grid-rows-1"
      >
        {/* Play Button */}
        <div
          className="row-span-2 flex items-center justify-center xl:col-span-1
            xl:row-span-1"
        >
          {maybeVideoURL && (
            <Link to={maybeVideoURL}>
              <PlayCircle className="inline" />
            </Link>
          )}
        </div>

        {/* Match Name */}
        <div
          className="row-span-2 flex items-center justify-center p-2
            xl:col-span-2 xl:row-span-1"
        >
          <span className="text-center">
            {matchTitleShort(match, playoffType)}
          </span>
        </div>

        {/* Red Team Players - Subgrid Component */}
        <TeamListSubgrid
          teamKeys={match.alliances.red.team_keys}
          allianceColor="red"
          className="col-span-3 xl:col-span-3"
          winner={match.winning_alliance === 'red'}
          dq={match.alliances.red.dq_team_keys}
          surrogate={match.alliances.red.surrogate_team_keys}
        />

        {/* Blue Team Players - Subgrid Component */}
        <TeamListSubgrid
          teamKeys={match.alliances.blue.team_keys}
          allianceColor="blue"
          className="col-span-3 xl:col-span-3"
          winner={match.winning_alliance === 'blue'}
          dq={match.alliances.blue.dq_team_keys}
          surrogate={match.alliances.blue.surrogate_team_keys}
        />

        {!isPlayed && (
          <div
            className="col-start-6 row-span-2 row-start-1 xl:col-span-2
              xl:col-start-auto xl:row-span-1 xl:row-start-auto"
          >
            <span className="flex h-full items-center justify-center">
              {match.predicted_time &&
                new Date(match.predicted_time * 1000).toLocaleTimeString(
                  'en-US',
                  {
                    hour: '2-digit',
                    minute: '2-digit',
                    weekday: 'short',
                    hour12: true,
                  },
                )}
            </span>
          </div>
        )}

        {/* Red Score */}
        {isPlayed && (
          <ScoreCell
            score={match.alliances.red.score}
            allianceColor="red"
            className="col-start-6 row-start-1 xl:col-span-1 xl:col-start-auto
              xl:row-start-auto"
            winner={match.winning_alliance === 'red'}
          />
        )}

        {/* Blue Score */}
        {isPlayed && (
          <ScoreCell
            score={match.alliances.blue.score}
            allianceColor="blue"
            className="col-start-6 row-start-2 xl:col-span-1 xl:col-start-auto
              xl:row-start-auto"
            winner={match.winning_alliance === 'blue'}
          />
        )}
      </div>
    </div>
  );
}

interface BreakRowProps extends React.HTMLAttributes<HTMLDivElement> {
  text: string;
}
export function BreakRow({ className, text, ...props }: BreakRowProps) {
  return (
    <div
      className={cn('col-span-11 flex rounded-md bg-muted', className)}
      {...props}
    >
      <span
        className="flex h-[1.25rem] w-full items-center justify-center text-xs
          font-bold"
      >
        {text}
      </span>
    </div>
  );
}
