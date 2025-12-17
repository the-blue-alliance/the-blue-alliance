import { Link } from '@tanstack/react-router';
import { MatchLink } from 'app/components/tba/links';

import PlayCircleIcon from '~icons/mdi/play-circle-outline';

import { Event, Match } from '~/api/tba/read';
import { ShouldInsertBreakCallback } from '~/components/tba/match/breakers';
import ScoreCell from '~/components/tba/match/scoreCell';
import TeamListSubgrid from '~/components/tba/match/teamListSubgrid';
import { PlayoffType } from '~/lib/api/PlayoffType';
import { matchTitleShort } from '~/lib/matchUtils';
import { cn } from '~/lib/utils';

export default function SimpleMatchRowsWithBreaks({
  matches,
  event,
  breakers,
  focusTeamKey,
}: {
  matches: Match[];
  event: Event;
  breakers: ShouldInsertBreakCallback[];
  focusTeamKey?: string;
}) {
  const divs = [];

  for (let i = 0; i < matches.length; i++) {
    const match = matches[i];
    const maybeNextMatch = i < matches.length - 1 ? matches[i + 1] : null;

    for (let bi = 0; bi < breakers.length; bi++) {
      const result = breakers[bi]({
        match,
        matchIndex: i,
        nextMatch: maybeNextMatch,
        event,
      });

      if (result.shouldBreak && result.whereToInsertBreak === 'before') {
        divs.push(
          <BreakRow
            key={`break-before-${i}-${bi}`}
            text={result.text ?? 'Break'}
          />,
        );
      }
    }

    divs.push(
      <MatchRow
        match={match}
        event={event}
        year={event.year}
        key={match.key}
        focusTeamKey={focusTeamKey}
      />,
    );

    for (let bi = 0; bi < breakers.length; bi++) {
      const result = breakers[bi]({
        match,
        matchIndex: i,
        nextMatch: maybeNextMatch,
        event,
      });

      if (result.shouldBreak && result.whereToInsertBreak === 'after') {
        divs.push(
          <BreakRow
            key={`break-after-${i}-${bi}`}
            text={result.text ?? 'Break'}
          />,
        );
      }
    }
  }

  return (
    <div
      className="flex flex-col divide-y *:odd:bg-gray-50 dark:*:odd:bg-gray-900"
    >
      {divs}
    </div>
  );
}

export function MatchRow({
  match,
  event,
  year,
  focusTeamKey,
}: {
  match: Match;
  event: Event;
  year: number;
  focusTeamKey?: string;
}) {
  const playoffType = event.playoff_type ?? PlayoffType.CUSTOM;
  const maybeVideoURL = maybeGetFirstMatchVideoURL(match);
  const isPlayed =
    match.alliances.red.score !== -1 && match.alliances.blue.score !== -1;

  /* Desktop: 1x11 grid, Mobile: 2x6 grid */
  return (
    <div
      className="mx-auto grid w-full max-w-6xl
        grid-cols-[2.5em_7em_repeat(4,1fr)] grid-rows-[2em_2em] gap-0.5 text-sm
        xl:grid-cols-[2.5em_7em_repeat(9,1fr)] xl:grid-rows-1"
    >
      {/* Play Button */}
      <div
        className="row-span-2 flex items-center justify-center rounded-tl-lg
          xl:col-span-1 xl:row-span-1 xl:rounded-l-lg"
      >
        {maybeVideoURL && (
          <Link
            to={maybeVideoURL}
            target="_blank"
            rel="noopener noreferrer"
            className="mx-2"
          >
            <PlayCircleIcon />
          </Link>
        )}
      </div>

      {/* Match Name */}
      <div
        className="row-span-2 flex items-center justify-center p-1.5
          xl:col-span-2 xl:row-span-1"
      >
        <MatchLink
          matchOrKey={match}
          event={event}
          className="text-center text-sm text-foreground"
        >
          {matchTitleShort(match, playoffType)}
        </MatchLink>
      </div>

      {/* Red Team Players - Subgrid Component */}
      <TeamListSubgrid
        teamKeys={match.alliances.red.team_keys}
        allianceColor="red"
        className="col-span-3 pt-0.5 xl:col-span-3 xl:pb-0.5"
        teamCellClassName="max-xl:first:rounded-tl-lg max-xl:last:rounded-tr-lg xl:first:rounded-l-lg"
        winner={match.winning_alliance === 'red'}
        dq={match.alliances.red.dq_team_keys}
        surrogate={match.alliances.red.surrogate_team_keys}
        year={year}
        focusTeamKey={focusTeamKey}
      />

      {/* Blue Team Players - Subgrid Component */}
      <TeamListSubgrid
        teamKeys={match.alliances.blue.team_keys}
        allianceColor="blue"
        className="col-span-3 pb-0.5 xl:col-span-3 xl:pt-0.5"
        teamCellClassName="max-xl:first:rounded-bl-lg max-xl:last:rounded-br-lg xl:last:rounded-r-lg"
        winner={match.winning_alliance === 'blue'}
        dq={match.alliances.blue.dq_team_keys}
        surrogate={match.alliances.blue.surrogate_team_keys}
        year={year}
        focusTeamKey={focusTeamKey}
      />

      {!isPlayed && (
        <div
          className="col-start-6 row-span-2 row-start-1 xl:col-span-2
            xl:col-start-auto xl:row-span-1 xl:row-start-auto"
        >
          <span className="flex h-full items-center justify-center text-center">
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
          className="col-start-6 row-start-1 mt-0.5 max-lg:rounded-t-lg
            xl:col-span-1 xl:col-start-auto xl:row-start-auto xl:mb-0.5
            xl:rounded-l-lg"
          winner={match.winning_alliance === 'red'}
          scoreBreakdown={match.score_breakdown?.red}
          year={year}
          compLevel={match.comp_level}
        />
      )}

      {/* Blue Score */}
      {isPlayed && (
        <ScoreCell
          score={match.alliances.blue.score}
          allianceColor="blue"
          className="col-start-6 row-start-2 mb-0.5 max-lg:rounded-b-lg
            xl:col-span-1 xl:col-start-auto xl:row-start-auto xl:mt-0.5
            xl:rounded-r-lg"
          winner={match.winning_alliance === 'blue'}
          scoreBreakdown={match.score_breakdown?.blue}
          year={year}
          compLevel={match.comp_level}
        />
      )}
    </div>
  );
}

// Used on match pages, omits the play button and match title
export function SimpleMatchRow({
  match,
  year,
}: {
  match: Match;
  year: number;
}) {
  const isPlayed =
    match.alliances.red.score !== -1 && match.alliances.blue.score !== -1;

  return (
    <div>
      {/* 3x4 grid with header row */}
      <div
        className="mx-auto grid w-full max-w-6xl grid-cols-[repeat(4,1fr)]
          grid-rows-[auto_repeat(2,2em)] gap-x-1 text-sm"
      >
        {/* Header: Teams */}
        <div
          className="col-span-3 col-start-1 row-start-1 flex items-center
            justify-center text-sm font-semibold"
        >
          Teams
        </div>

        {/* Header: Score */}
        <div
          className="col-start-4 row-start-1 flex items-center justify-center
            text-sm font-semibold"
        >
          Score
        </div>

        {/* Red Team Players - Subgrid Component */}
        <TeamListSubgrid
          teamKeys={match.alliances.red.team_keys}
          allianceColor="red"
          className="col-span-3 col-start-1 row-start-2"
          teamCellClassName="first:rounded-tl-lg last:rounded-tr-lg"
          winner={match.winning_alliance === 'red'}
          dq={match.alliances.red.dq_team_keys}
          surrogate={match.alliances.red.surrogate_team_keys}
          year={year}
        />

        {/* Blue Team Players - Subgrid Component */}
        <TeamListSubgrid
          teamKeys={match.alliances.blue.team_keys}
          allianceColor="blue"
          className="col-span-3 col-start-1 row-start-3"
          teamCellClassName="first:rounded-bl-lg last:rounded-br-lg"
          winner={match.winning_alliance === 'blue'}
          dq={match.alliances.blue.dq_team_keys}
          surrogate={match.alliances.blue.surrogate_team_keys}
          year={year}
        />

        {!isPlayed && (
          <div
            className="col-start-4 row-span-2 row-start-2 flex items-center
              justify-center text-center"
          >
            <span>
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
            className="col-start-4 row-start-2 rounded-tl-lg rounded-tr-lg"
            winner={match.winning_alliance === 'red'}
            scoreBreakdown={match.score_breakdown?.red}
            year={year}
            compLevel={match.comp_level}
          />
        )}

        {/* Blue Score */}
        {isPlayed && (
          <ScoreCell
            score={match.alliances.blue.score}
            allianceColor="blue"
            className="col-start-4 row-start-3 rounded-br-lg rounded-bl-lg"
            winner={match.winning_alliance === 'blue'}
            scoreBreakdown={match.score_breakdown?.blue}
            year={year}
            compLevel={match.comp_level}
          />
        )}
      </div>
    </div>
  );
}

function maybeGetFirstMatchVideoURL(match: Match): string | undefined {
  if (match.videos.length === 0) {
    return undefined;
  }

  return `https://www.youtube.com/watch?v=${match.videos[0].key}`;
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
        className="flex h-8 w-full items-center justify-center text-xs
          font-medium"
      >
        {text}
      </span>
    </div>
  );
}
