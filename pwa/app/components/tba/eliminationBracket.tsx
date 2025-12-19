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
import {
  EliminationBracketPaths,
  PlayoffMatchHandle,
  useAdvancementPaths,
} from '~/components/tba/eliminationBracketPaths';
import { MatchLink, TeamLink } from '~/components/tba/links';
import { Card, CardHeader, CardTitle } from '~/components/ui/card';
import { EventType } from '~/lib/api/EventType';
import { getDivisionShortform } from '~/lib/eventUtils';
import { sortMatchComparator } from '~/lib/matchUtils';
import { cn } from '~/lib/utils';

export type MatchLabel =
  | 'Match 1'
  | 'Match 2'
  | 'Match 3'
  | 'Match 4'
  | 'Match 5'
  | 'Match 6'
  | 'Match 7'
  | 'Match 8'
  | 'Match 9'
  | 'Match 10'
  | 'Match 11'
  | 'Match 12'
  | 'Match 13'
  | 'Finals';

type MatchResult = {
  score: number;
  won: boolean;
};

export interface SeriesResult {
  redTeams: string[];
  blueTeams: string[];
  redAllianceNumber: number | null;
  blueAllianceNumber: number | null;
  redResults: MatchResult[]; // For each match in the set
  blueResults: MatchResult[]; // For each match in the set
  redWon: boolean; // Overall winner of the series
  blueWon: boolean; // Overall winner of the series
  matchRedTeams: string[];
  matchBlueTeams: string[];
}

const PlayoffMatch = forwardRef<
  PlayoffMatchHandle,
  {
    matchLabel: MatchLabel;
    matches: Match[] | undefined;
    event: Event;
    hoveredAlliance: number | null;
    setHoveredAlliance: Dispatch<SetStateAction<number | null>>;
    getSeriesResult: (matches: Match[] | undefined) => SeriesResult | null;
    getAllianceDisplayName: (allianceNumber: number) => string;
    showFullAllliance?: boolean;
  }
>(function PlayoffMatch(
  {
    matchLabel,
    matches,
    event,
    hoveredAlliance,
    setHoveredAlliance,
    getSeriesResult,
    getAllianceDisplayName,
    showFullAllliance = false,
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
          {matches?.map((match) => {
            return (
              <MatchLink
                key={match.key}
                matchOrKey={match}
                event={event}
                className="flex items-center justify-center"
              >
                <PlayCircleIcon className="inline size-4" />
              </MatchLink>
            );
          })}
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
              if (!teamPlayed && !showFullAllliance) {
                return null;
              }
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
              if (!teamPlayed && !showFullAllliance) {
                return null;
              }
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

export default function EliminationBracket({
  alliances,
  matches,
  event,
}: {
  alliances: EliminationAlliance[];
  matches: Match[];
  event: Event;
}): JSX.Element {
  const [hoveredAlliance, setHoveredAlliance] = useState<number | null>(null);
  const matchRefs = useRef<Record<MatchLabel, PlayoffMatchHandle | null>>({
    'Match 1': null,
    'Match 2': null,
    'Match 3': null,
    'Match 4': null,
    'Match 5': null,
    'Match 6': null,
    'Match 7': null,
    'Match 8': null,
    'Match 9': null,
    'Match 10': null,
    'Match 11': null,
    'Match 12': null,
    'Match 13': null,
    Finals: null,
  });
  const containerRef = useRef<HTMLDivElement>(null);

  // Helper to get alliance display name
  const getAllianceDisplayName = (allianceNumber: number): string => {
    if (!allianceNumber || allianceNumber > alliances.length) return '';

    const alliance = alliances[allianceNumber - 1];
    if (event.event_type === EventType.CMP_FINALS && alliance.name) {
      // For Einstein events, use division shortform if available
      return getDivisionShortform(alliance.name);
    }
    // Default to alliance number
    return `#${allianceNumber}`;
  };

  // Group matches by set_number.
  const matchesBySet = useMemo(() => {
    const grouped = [...matches]
      .filter((m) => m.comp_level === 'sf') // Non-finals double elim matches are all sf
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

  // Helper to get alliance numbers for teams
  const getAllianceNumber = (teamKeys: string[]): number | null => {
    for (let i = 0; i < alliances.length; i++) {
      // Check if all team keys match this alliance
      const allianceTeamKeys = alliances[i].picks.map((pick) =>
        pick.substring(3),
      );
      if (teamKeys.every((team) => allianceTeamKeys.includes(team))) {
        return i + 1; // Alliance numbers are 1-based
      }
    }
    return null;
  };

  // Helper to get match result
  const getSeriesResult = (
    setMatches: Match[] | undefined,
  ): SeriesResult | null => {
    if (!setMatches || setMatches.length === 0) return null;

    // Use the first match to get team information (they should be the same across the series)
    const matchRedTeams = setMatches[0].alliances.red.team_keys.map((t) =>
      t.substring(3),
    );
    const matchBlueTeams = setMatches[0].alliances.blue.team_keys.map((t) =>
      t.substring(3),
    );

    // Get alliance numbers and full alliance rosters
    const redAllianceNumber = getAllianceNumber(matchRedTeams);
    const blueAllianceNumber = getAllianceNumber(matchBlueTeams);

    // Get full alliance rosters (all teams, not just the 3 that played)
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

    // Determine overall winner from the series
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
      matchRedTeams, // Teams that actually played
      matchBlueTeams, // Teams that actually played
    };
  };

  const { paths, svgSize } = useAdvancementPaths({
    containerRef,
    matchRefs,
    matchesBySet,
    finalsMatches,
    getSeriesResult,
  });

  if (alliances.length === 0 || matches.length === 0) {
    return <></>;
  }

  return (
    <Card className="mt-12 bg-neutral-50/50 p-2 dark:bg-neutral-900/50">
      <CardHeader>
        <CardTitle>Playoff Bracket</CardTitle>
      </CardHeader>

      <div className="overflow-x-auto overflow-y-hidden">
        <div
          ref={containerRef}
          className="relative isolate flex min-w-max items-start justify-start
            gap-6 px-4"
        >
          {/* Bracket Layout */}
          <div className="relative z-1 space-y-4">
            {/* Upper Bracket */}
            <div className="space-y-4">
              <h2 className="text-center text-xl font-medium">Upper Bracket</h2>
              <div className="flex items-start gap-8">
                {/* Round 1 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center">Round 1</h3>
                  <div className="space-y-4">
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 1'] = node;
                      }}
                      matchLabel="Match 1"
                      matches={matchesBySet[1]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                      showFullAllliance
                    />
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 2'] = node;
                      }}
                      matchLabel="Match 2"
                      matches={matchesBySet[2]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                      showFullAllliance
                    />
                    <div className="h-6"></div>
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 3'] = node;
                      }}
                      matchLabel="Match 3"
                      matches={matchesBySet[3]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                      showFullAllliance
                    />
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 4'] = node;
                      }}
                      matchLabel="Match 4"
                      matches={matchesBySet[4]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                      showFullAllliance
                    />
                  </div>
                </div>

                {/* Round 2 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center">Round 2</h3>
                  <div className="space-y-4">
                    <div className="h-4"></div>
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 7'] = node;
                      }}
                      matchLabel="Match 7"
                      matches={matchesBySet[7]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                    />
                    <div className="h-28"></div>
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 8'] = node;
                      }}
                      matchLabel="Match 8"
                      matches={matchesBySet[8]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                    />
                  </div>
                </div>

                {/* Round 4 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center">Round 4</h3>
                  <div className="space-y-4">
                    <div className="h-32"></div>
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 11'] = node;
                      }}
                      matchLabel="Match 11"
                      matches={matchesBySet[11]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                    />
                  </div>
                </div>

                <div className="w-32"></div>

                {/* Finals */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center font-bold">Finals</h3>
                  <div className="space-y-4">
                    <div className="h-32"></div>
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current.Finals = node;
                      }}
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

            {/* Lower Bracket */}
            <div className="space-y-4">
              <h2 className="text-center text-xl font-medium">Lower Bracket</h2>
              <div className="ml-16 flex items-start gap-8">
                {/* Round 2 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center">Round 2</h3>
                  <div className="space-y-4">
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 5'] = node;
                      }}
                      matchLabel="Match 5"
                      matches={matchesBySet[5]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                    />
                    <div className="h-6"></div>
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 6'] = node;
                      }}
                      matchLabel="Match 6"
                      matches={matchesBySet[6]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                    />
                  </div>
                </div>

                {/* Round 3 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center">Round 3</h3>
                  <div className="space-y-4">
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 10'] = node;
                      }}
                      matchLabel="Match 10"
                      matches={matchesBySet[10]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                    />
                    <div className="h-6"></div>
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 9'] = node;
                      }}
                      matchLabel="Match 9"
                      matches={matchesBySet[9]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                    />
                  </div>
                </div>

                {/* Round 4 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center">Round 4</h3>
                  <div className="space-y-4">
                    <div className="h-8"></div>
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 12'] = node;
                      }}
                      matchLabel="Match 12"
                      matches={matchesBySet[12]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                    />
                  </div>
                </div>

                {/* Round 5 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center">Round 5</h3>
                  <div className="space-y-4">
                    <div className="h-8"></div>
                    <PlayoffMatch
                      ref={(node) => {
                        matchRefs.current['Match 13'] = node;
                      }}
                      matchLabel="Match 13"
                      matches={matchesBySet[13]}
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

          <EliminationBracketPaths
            paths={paths}
            svgSize={svgSize}
            hoveredAlliance={hoveredAlliance}
          />
        </div>
      </div>
    </Card>
  );
}
