import {
  type Dispatch,
  type JSX,
  type SetStateAction,
  forwardRef,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';

import PlayCircleIcon from '~icons/mdi/play-circle-outline';

import { EliminationAlliance, Event, Match } from '~/api/tba/read';
import { MatchLink, TeamLink } from '~/components/tba/links';
import { Card, CardHeader, CardTitle } from '~/components/ui/card';
import { EventType } from '~/lib/api/EventType';
import { getDivisionShortform } from '~/lib/eventUtils';
import { sortMatchComparator } from '~/lib/matchUtils';
import { cn } from '~/lib/utils';

type MatchLabel4 =
  | 'Match 1'
  | 'Match 2'
  | 'Match 3'
  | 'Match 4'
  | 'Match 5'
  | 'Finals';

type MatchResult = {
  score: number;
  won: boolean;
};

type SeriesResult = {
  redTeams: string[];
  blueTeams: string[];
  redAllianceNumber: number | null;
  blueAllianceNumber: number | null;
  redResults: MatchResult[];
  blueResults: MatchResult[];
  redWon: boolean;
  blueWon: boolean;
  matchRedTeams: string[];
  matchBlueTeams: string[];
};

type MatchHandle = {
  card: HTMLDivElement | null;
  redRow: HTMLDivElement | null;
  blueRow: HTMLDivElement | null;
  redAlliance: number | null;
  blueAlliance: number | null;
};

const BracketMatch = forwardRef<
  MatchHandle,
  {
    matchLabel: MatchLabel4;
    matches: Match[] | undefined;
    event: Event;
    hoveredAlliance: number | null;
    setHoveredAlliance: Dispatch<SetStateAction<number | null>>;
    getSeriesResult: (matches: Match[] | undefined) => SeriesResult | null;
    getAllianceDisplayName: (allianceNumber: number) => string;
    showFullAlliance?: boolean;
  }
>(function BracketMatch(
  {
    matchLabel,
    matches,
    event,
    hoveredAlliance,
    setHoveredAlliance,
    getSeriesResult,
    getAllianceDisplayName,
    showFullAlliance = false,
  },
  ref,
): JSX.Element | null {
  const cardRef = useRef<HTMLDivElement>(null);
  const redRowRef = useRef<HTMLDivElement>(null);
  const blueRowRef = useRef<HTMLDivElement>(null);
  const result = getSeriesResult(matches);

  useImperativeHandle(ref, () => ({
    card: cardRef.current,
    redRow: redRowRef.current,
    blueRow: blueRowRef.current,
    redAlliance: result?.redAllianceNumber ?? null,
    blueAlliance: result?.blueAllianceNumber ?? null,
  }));

  if (!result) return null;

  const isRedHighlighted = hoveredAlliance === result.redAllianceNumber;
  const isBlueHighlighted = hoveredAlliance === result.blueAllianceNumber;
  const isHighlighted = isRedHighlighted || isBlueHighlighted;

  return (
    <div
      ref={cardRef}
      className={cn(
        `mb-2 min-w-45 overflow-hidden rounded-md border border-neutral-200
        bg-background transition-all duration-200 dark:border-neutral-700`,
        {
          [`border-transparent shadow-lg ring-2 ring-alliance-red/75
          dark:border-transparent`]: isHighlighted && result.redWon,
          [`border-transparent shadow-lg ring-2 ring-alliance-blue/75
          dark:border-transparent`]: isHighlighted && result.blueWon,
        },
      )}
    >
      <div
        className="flex items-center justify-between border-b px-2 py-1 text-sm
          font-bold"
      >
        <div className="flex items-center gap-1">
          <span>{matchLabel}</span>
          {result.redAllianceNumber && result.blueAllianceNumber && (
            <span className="text-xs font-normal">
              (
              <span
                className={cn(
                  'text-alliance-red transition-all duration-200',
                  isRedHighlighted &&
                    `rounded bg-red-100 px-1 text-sm dark:bg-red-900
                    dark:text-white`,
                )}
              >
                {getAllianceDisplayName(result.redAllianceNumber)}
              </span>{' '}
              vs{' '}
              <span
                className={cn(
                  'text-alliance-blue transition-all duration-200',
                  isBlueHighlighted &&
                    `rounded bg-blue-100 px-1 text-sm dark:bg-blue-900
                    dark:text-white`,
                )}
              >
                {getAllianceDisplayName(result.blueAllianceNumber)}
              </span>
              )
            </span>
          )}
        </div>
        <div className="flex items-center gap-5">
          {matches?.map((match) => (
            <MatchLink
              key={match.key}
              matchOrKey={match}
              event={event}
              className="flex items-center justify-center"
            >
              <PlayCircleIcon className="inline size-4" />
            </MatchLink>
          ))}
        </div>
      </div>
      <div
        className={`group flex cursor-pointer items-center justify-between
          bg-alliance-red/15 px-1 py-1 transition-colors duration-200
          data-[highlight=true]:bg-alliance-red
          data-[highlight=true]:text-white`}
        data-highlight={isRedHighlighted}
        ref={redRowRef}
        onMouseEnter={() =>
          result.redAllianceNumber &&
          setHoveredAlliance(result.redAllianceNumber)
        }
        onMouseLeave={() => setHoveredAlliance(null)}
      >
        <div className="flex flex-1 items-center justify-start">
          <div className="flex">
            {result.redTeams.map((team) => {
              const teamPlayed = result.matchRedTeams.includes(team);
              if (!teamPlayed && !showFullAlliance) return null;
              return (
                <span
                  key={team}
                  className={cn(
                    `w-12 text-center text-sm text-alliance-red
                    group-data-[highlight=true]:text-white`,
                    result.redWon && 'font-bold',
                    !teamPlayed &&
                      'underline decoration-current decoration-dotted',
                  )}
                >
                  <TeamLink
                    className="text-inherit"
                    teamOrKey={`frc${team}`}
                    year={event.year}
                  >
                    {team}
                  </TeamLink>
                </span>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <div className="flex min-w-0 gap-1">
            {result.redResults.map((r, i) => (
              <span
                key={i}
                className={cn(
                  'w-8 shrink-0 text-center text-sm',
                  r.won && 'font-bold',
                )}
              >
                {r.score !== -1 ? r.score : '-'}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div
        className={`group flex cursor-pointer items-center justify-between
          bg-alliance-blue/15 px-1 py-1 transition-colors duration-200
          data-[highlight=true]:bg-alliance-blue
          data-[highlight=true]:text-white`}
        data-highlight={isBlueHighlighted}
        ref={blueRowRef}
        onMouseEnter={() =>
          result.blueAllianceNumber &&
          setHoveredAlliance(result.blueAllianceNumber)
        }
        onMouseLeave={() => setHoveredAlliance(null)}
      >
        <div className="flex flex-1 items-center justify-start">
          <div className="flex">
            {result.blueTeams.map((team) => {
              const teamPlayed = result.matchBlueTeams.includes(team);
              if (!teamPlayed && !showFullAlliance) return null;
              return (
                <span
                  key={team}
                  className={cn(
                    `w-12 text-center text-sm text-alliance-blue
                    group-data-[highlight=true]:text-white`,
                    result.blueWon && 'font-bold',
                    !teamPlayed &&
                      'underline decoration-current decoration-dotted',
                  )}
                >
                  <TeamLink
                    className="text-inherit"
                    teamOrKey={`frc${team}`}
                    year={event.year}
                  >
                    {team}
                  </TeamLink>
                </span>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <div className="flex min-w-0 gap-1">
            {result.blueResults.map((r, i) => (
              <span
                key={i}
                className={cn(
                  'w-8 flex-shrink-0 text-center text-sm',
                  r.won && 'font-bold',
                )}
              >
                {r.score !== -1 ? r.score : '-'}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
});

export default function DoubleElim4TeamBracket({
  alliances,
  matches,
  event,
}: {
  alliances: EliminationAlliance[];
  matches: Match[];
  event: Event;
}): JSX.Element {
  const [hoveredAlliance, setHoveredAlliance] = useState<number | null>(null);

  // Group SF matches by set_number, Finals separately
  const matchesBySet = useMemo(() => {
    const grouped = [...matches]
      .filter((m) => m.comp_level === 'sf')
      .reduce<Record<number, Match[]>>((acc, match) => {
        (acc[match.set_number] ??= []).push(match);
        return acc;
      }, {});
    Object.values(grouped).forEach((setMatches) =>
      setMatches.sort(sortMatchComparator),
    );
    return grouped;
  }, [matches]);

  const finalsMatches = useMemo(
    () => matches.filter((m) => m.comp_level === 'f').sort(sortMatchComparator),
    [matches],
  );

  const getAllianceNumber = (teamKeys: string[]): number | null => {
    for (let i = 0; i < alliances.length; i++) {
      const allianceTeamKeys = alliances[i].picks.map((pick) =>
        pick.substring(3),
      );
      if (teamKeys.every((team) => allianceTeamKeys.includes(team))) {
        return i + 1;
      }
    }
    return null;
  };

  const getAllianceDisplayName = (allianceNumber: number): string => {
    if (!allianceNumber || allianceNumber > alliances.length) return '';
    const alliance = alliances[allianceNumber - 1];
    if (event.event_type === EventType.CMP_FINALS && alliance.name) {
      return getDivisionShortform(alliance.name);
    }
    return `#${allianceNumber}`;
  };

  const getSeriesResult = (
    setMatches: Match[] | undefined,
  ): SeriesResult | null => {
    if (!setMatches || setMatches.length === 0) return null;

    const matchRedTeams = setMatches[0].alliances.red.team_keys.map((t) =>
      t.substring(3),
    );
    const matchBlueTeams = setMatches[0].alliances.blue.team_keys.map((t) =>
      t.substring(3),
    );

    const redAllianceNumber = getAllianceNumber(matchRedTeams);
    const blueAllianceNumber = getAllianceNumber(matchBlueTeams);

    const redTeams = redAllianceNumber
      ? alliances[redAllianceNumber - 1].picks.map((pick) => pick.substring(3))
      : matchRedTeams;
    const blueTeams = blueAllianceNumber
      ? alliances[blueAllianceNumber - 1].picks.map((pick) => pick.substring(3))
      : matchBlueTeams;

    const redResults = setMatches.map((match) => ({
      score: match.alliances.red.score,
      won: match.winning_alliance === 'red',
    }));
    const blueResults = setMatches.map((match) => ({
      score: match.alliances.blue.score,
      won: match.winning_alliance === 'blue',
    }));

    const lastMatch = setMatches[setMatches.length - 1];
    const redWon = lastMatch.winning_alliance === 'red';
    const blueWon = lastMatch.winning_alliance === 'blue';

    return {
      redTeams,
      blueTeams,
      redAllianceNumber,
      blueAllianceNumber,
      redResults,
      blueResults,
      redWon,
      blueWon,
      matchRedTeams,
      matchBlueTeams,
    };
  };

  if (alliances.length === 0 || matches.length === 0) {
    return <></>;
  }

  return (
    <Card className="mt-12 bg-neutral-50/50 p-2 dark:bg-neutral-900/50">
      <CardHeader>
        <CardTitle>Playoff Bracket</CardTitle>
      </CardHeader>

      <div className="overflow-x-auto overflow-y-hidden">
        <div className="flex min-w-max items-start justify-start gap-6 px-4">
          {/* Upper Bracket */}
          <div className="space-y-4">
            <h2 className="text-center text-xl font-medium">Upper Bracket</h2>
            <div className="flex items-start gap-8">
              {/* Round 1 */}
              <div className="flex flex-col items-center">
                <h3 className="mb-4 text-center">Round 1</h3>
                <div className="space-y-4">
                  <BracketMatch
                    matchLabel="Match 1"
                    matches={matchesBySet[1]}
                    event={event}
                    hoveredAlliance={hoveredAlliance}
                    setHoveredAlliance={setHoveredAlliance}
                    getSeriesResult={getSeriesResult}
                    getAllianceDisplayName={getAllianceDisplayName}
                    showFullAlliance
                  />
                  <BracketMatch
                    matchLabel="Match 2"
                    matches={matchesBySet[2]}
                    event={event}
                    hoveredAlliance={hoveredAlliance}
                    setHoveredAlliance={setHoveredAlliance}
                    getSeriesResult={getSeriesResult}
                    getAllianceDisplayName={getAllianceDisplayName}
                    showFullAlliance
                  />
                </div>
              </div>

              {/* Round 2 - Upper */}
              <div className="flex flex-col items-center">
                <h3 className="mb-4 text-center">Round 2</h3>
                <div className="space-y-4">
                  <div className="h-8"></div>
                  <BracketMatch
                    matchLabel="Match 4"
                    matches={matchesBySet[4]}
                    event={event}
                    hoveredAlliance={hoveredAlliance}
                    setHoveredAlliance={setHoveredAlliance}
                    getSeriesResult={getSeriesResult}
                    getAllianceDisplayName={getAllianceDisplayName}
                  />
                </div>
              </div>

              <div className="w-16"></div>

              {/* Finals */}
              <div className="flex flex-col items-center">
                <h3 className="mb-4 text-center font-bold">Finals</h3>
                <div className="space-y-4">
                  <div className="h-8"></div>
                  <BracketMatch
                    matchLabel="Finals"
                    matches={finalsMatches}
                    event={event}
                    hoveredAlliance={hoveredAlliance}
                    setHoveredAlliance={setHoveredAlliance}
                    getSeriesResult={getSeriesResult}
                    getAllianceDisplayName={getAllianceDisplayName}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Lower Bracket */}
        <div className="mt-6 px-4">
          <div className="space-y-4">
            <h2 className="text-center text-xl font-medium">Lower Bracket</h2>
            <div className="ml-16 flex items-start gap-8">
              {/* Round 2 - Lower */}
              <div className="flex flex-col items-center">
                <h3 className="mb-4 text-center">Round 2</h3>
                <div className="space-y-4">
                  <BracketMatch
                    matchLabel="Match 3"
                    matches={matchesBySet[3]}
                    event={event}
                    hoveredAlliance={hoveredAlliance}
                    setHoveredAlliance={setHoveredAlliance}
                    getSeriesResult={getSeriesResult}
                    getAllianceDisplayName={getAllianceDisplayName}
                  />
                </div>
              </div>

              {/* Round 3 - Lower */}
              <div className="flex flex-col items-center">
                <h3 className="mb-4 text-center">Round 3</h3>
                <div className="space-y-4">
                  <BracketMatch
                    matchLabel="Match 5"
                    matches={matchesBySet[5]}
                    event={event}
                    hoveredAlliance={hoveredAlliance}
                    setHoveredAlliance={setHoveredAlliance}
                    getSeriesResult={getSeriesResult}
                    getAllianceDisplayName={getAllianceDisplayName}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
