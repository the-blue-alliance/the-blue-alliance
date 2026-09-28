import { cn } from 'cn';
import {
  type Dispatch,
  type JSX,
  type SetStateAction,
  forwardRef,
  memo,
  useCallback,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';

import PlayCircleIcon from '~icons/mdi/play-circle-outline';

import {
  AllianceColor,
  CompLevel,
  EliminationAlliance,
  Event,
  EventType,
  Match,
} from '~/api/tba/read';
import BracketPlaceholderMatch from '~/components/tba/bracketPlaceholderMatch';
import BracketViewThroughSelect, {
  VIEW_ALL_MATCHES,
  matchesViewedThrough,
} from '~/components/tba/bracketViewThroughSelect';
import {
  EliminationBracketPaths,
  type PlayoffMatchHandle,
  type SeriesResult,
  type WinnerLink,
  useAdvancementPaths,
} from '~/components/tba/eliminationBracketPaths';
import { MatchLink } from '~/components/tba/links';
import { TeamLinkWithTooltip } from '~/components/tba/teamTooltip';
import { Badge } from '~/components/ui/badge';
import { Card, CardHeader, CardTitle } from '~/components/ui/card';
import {
  type BracketSides,
  DOUBLE_ELIM_4_SLOTS,
  nextSeriesLabel,
  resolveBracketSides,
  seriesOutcome,
  sideAllianceNumber,
} from '~/lib/doubleElimBracket';
import { getDivisionShortform } from '~/lib/eventUtils';
import { sortMatchComparator } from '~/lib/matchUtils';

type MatchLabel4 =
  'Match 1' | 'Match 2' | 'Match 3' | 'Match 4' | 'Match 5' | 'Finals';

const WINNER_LINKS: WinnerLink[] = [
  { from: 'Match 1', to: 'Match 3' },
  { from: 'Match 2', to: 'Match 3' },
  { from: 'Match 3', to: 'Finals' },
  { from: 'Match 4', to: 'Match 5' },
  { from: 'Match 5', to: 'Finals' },
];

const _BracketMatch = forwardRef<
  PlayoffMatchHandle,
  {
    matchLabel: MatchLabel4;
    matches: Match[] | undefined;
    sides: BracketSides;
    alliances: EliminationAlliance[];
    event: Event;
    hoveredAlliance: number | null;
    setHoveredAlliance: Dispatch<SetStateAction<number | null>>;
    getSeriesResult: (matches: Match[] | undefined) => SeriesResult | null;
    getAllianceDisplayName: (allianceNumber: number) => string;
    isNext: boolean;
    showFullAlliance?: boolean;
  }
>(function BracketMatch(
  {
    matchLabel,
    matches,
    sides,
    alliances,
    event,
    hoveredAlliance,
    setHoveredAlliance,
    getSeriesResult,
    getAllianceDisplayName,
    isNext,
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
    redAlliance: result?.redAllianceNumber ?? sideAllianceNumber(sides.red),
    blueAlliance: result?.blueAllianceNumber ?? sideAllianceNumber(sides.blue),
  }));

  if (!result) {
    return (
      <BracketPlaceholderMatch
        matchLabel={matchLabel}
        sides={sides}
        alliances={alliances}
        event={event}
        hoveredAlliance={hoveredAlliance}
        setHoveredAlliance={setHoveredAlliance}
        getAllianceDisplayName={getAllianceDisplayName}
        cardRef={cardRef}
        redRowRef={redRowRef}
        blueRowRef={blueRowRef}
        isNext={isNext}
      />
    );
  }

  const isRedHighlighted = hoveredAlliance === result.redAllianceNumber;
  const isBlueHighlighted = hoveredAlliance === result.blueAllianceNumber;
  const isHighlighted = isRedHighlighted || isBlueHighlighted;

  return (
    <div
      ref={cardRef}
      role="group"
      aria-label={matchLabel}
      className={cn(
        `mb-2 min-w-45 overflow-hidden rounded-md border border-neutral-200
        bg-background transition-all duration-200 dark:border-neutral-700`,
        {
          [`border-transparent shadow-lg ring-2 ring-alliance-red-accent/75
          dark:border-transparent`]: isHighlighted && result.redWon,
          [`border-transparent shadow-lg ring-2 ring-alliance-blue-accent/75
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
                  'transition-all duration-200',
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
                  'transition-all duration-200',
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
          {isNext && <Badge variant="success">Next</Badge>}
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
        className={`flex cursor-pointer items-center justify-between
          bg-alliance-red-loser px-1 py-1 transition-colors duration-200
          data-[highlight=true]:ring-2 data-[highlight=true]:ring-foreground
          data-[highlight=true]:ring-inset
          data-[winner=true]:bg-alliance-red-winner`}
        data-highlight={isRedHighlighted}
        data-winner={result.redWon}
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
                    'w-12 text-center text-sm',
                    result.redWon && 'font-bold',
                    !teamPlayed &&
                      'underline decoration-current decoration-dotted',
                  )}
                >
                  <TeamLinkWithTooltip
                    className="text-inherit"
                    teamKey={`frc${team}`}
                    year={event.year}
                  />
                </span>
              );
            })}
          </div>
        </div>
        <div
          className="flex items-center gap-1 self-stretch border-l
            border-current/20 pl-1"
        >
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
        className={`flex cursor-pointer items-center justify-between
          bg-alliance-blue-loser px-1 py-1 transition-colors duration-200
          data-[highlight=true]:ring-2 data-[highlight=true]:ring-foreground
          data-[highlight=true]:ring-inset
          data-[winner=true]:bg-alliance-blue-winner`}
        data-highlight={isBlueHighlighted}
        data-winner={result.blueWon}
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
                    'w-12 text-center text-sm',
                    result.blueWon && 'font-bold',
                    !teamPlayed &&
                      'underline decoration-current decoration-dotted',
                  )}
                >
                  <TeamLinkWithTooltip
                    className="text-inherit"
                    teamKey={`frc${team}`}
                    year={event.year}
                  />
                </span>
              );
            })}
          </div>
        </div>
        <div
          className="flex items-center gap-1 self-stretch border-l
            border-current/20 pl-1"
        >
          <div className="flex min-w-0 gap-1">
            {result.blueResults.map((r, i) => (
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
    </div>
  );
});

const BracketMatch = memo(_BracketMatch, (prev, next) => {
  if (
    prev.matches !== next.matches ||
    prev.sides !== next.sides ||
    prev.alliances !== next.alliances ||
    prev.event !== next.event ||
    prev.matchLabel !== next.matchLabel ||
    prev.isNext !== next.isNext ||
    prev.getSeriesResult !== next.getSeriesResult ||
    prev.getAllianceDisplayName !== next.getAllianceDisplayName ||
    prev.setHoveredAlliance !== next.setHoveredAlliance
  ) {
    return false;
  }
  const result = next.getSeriesResult(next.matches);
  const red = result?.redAllianceNumber ?? sideAllianceNumber(next.sides.red);
  const blue =
    result?.blueAllianceNumber ?? sideAllianceNumber(next.sides.blue);
  return (
    (prev.hoveredAlliance === red) === (next.hoveredAlliance === red) &&
    (prev.hoveredAlliance === blue) === (next.hoveredAlliance === blue)
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
  const [viewThrough, setViewThrough] = useState(VIEW_ALL_MATCHES);
  const visibleMatches = useMemo(
    () => matchesViewedThrough(matches, viewThrough),
    [matches, viewThrough],
  );
  const matchRefs = useRef<Record<MatchLabel4, PlayoffMatchHandle | null>>({
    'Match 1': null,
    'Match 2': null,
    'Match 3': null,
    'Match 4': null,
    'Match 5': null,
    Finals: null,
  });
  const containerRef = useRef<HTMLDivElement>(null);

  // Group SF matches by set_number, Finals separately
  const matchesBySet = useMemo(() => {
    const grouped = [...visibleMatches]
      .filter((m) => m.comp_level === CompLevel.SF)
      .reduce<Record<number, Match[]>>((acc, match) => {
        (acc[match.set_number] ??= []).push(match);
        return acc;
      }, {});
    Object.values(grouped).forEach((setMatches) =>
      setMatches.sort(sortMatchComparator),
    );
    return grouped;
  }, [visibleMatches]);

  const finalsMatches = useMemo(
    () =>
      visibleMatches
        .filter((m) => m.comp_level === CompLevel.F)
        .sort(sortMatchComparator),
    [visibleMatches],
  );

  const getAllianceNumber = useCallback(
    (teamKeys: string[]): number | null => {
      for (let i = 0; i < alliances.length; i++) {
        const allianceTeamKeys = alliances[i].picks.map((pick) =>
          pick.substring(3),
        );
        if (teamKeys.every((team) => allianceTeamKeys.includes(team))) {
          return i + 1;
        }
      }
      return null;
    },
    [alliances],
  );

  const getAllianceDisplayName = useCallback(
    (allianceNumber: number): string => {
      if (!allianceNumber || allianceNumber > alliances.length) return '';
      const alliance = alliances[allianceNumber - 1];
      if (event.event_type === EventType.CMP_FINALS && alliance.name) {
        return getDivisionShortform(alliance.name);
      }
      return `#${allianceNumber}`;
    },
    [alliances, event.event_type],
  );

  const getSeriesResult = useCallback(
    (setMatches: Match[] | undefined): SeriesResult | null => {
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
        ? alliances[redAllianceNumber - 1].picks.map((pick) =>
            pick.substring(3),
          )
        : matchRedTeams;
      const blueTeams = blueAllianceNumber
        ? alliances[blueAllianceNumber - 1].picks.map((pick) =>
            pick.substring(3),
          )
        : matchBlueTeams;

      const redResults = setMatches.map((match) => ({
        score: match.alliances.red.score,
        won: match.winning_alliance === AllianceColor.RED,
      }));
      const blueResults = setMatches.map((match) => ({
        score: match.alliances.blue.score,
        won: match.winning_alliance === AllianceColor.BLUE,
      }));

      const lastMatch = setMatches[setMatches.length - 1];
      const redWon = lastMatch.winning_alliance === AllianceColor.RED;
      const blueWon = lastMatch.winning_alliance === AllianceColor.BLUE;

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
    },
    [alliances, getAllianceNumber],
  );

  const matchLookup: Record<string, Match[] | undefined> = useMemo(
    () => ({
      'Match 1': matchesBySet[1],
      'Match 2': matchesBySet[2],
      'Match 3': matchesBySet[3],
      'Match 4': matchesBySet[4],
      'Match 5': matchesBySet[5],
      Finals: finalsMatches,
    }),
    [matchesBySet, finalsMatches],
  );

  const sides = useMemo(
    () =>
      resolveBracketSides(
        DOUBLE_ELIM_4_SLOTS,
        Object.fromEntries(
          Object.entries(matchLookup).map(([label, setMatches]) => [
            label,
            seriesOutcome(getSeriesResult(setMatches)),
          ]),
        ),
      ),
    [matchLookup, getSeriesResult],
  );

  const nextLabel = useMemo(() => nextSeriesLabel(matchLookup), [matchLookup]);

  const { paths, svgSize } = useAdvancementPaths({
    containerRef,
    matchRefs,
    winnerLinks: WINNER_LINKS,
    matchLookup,
    getSeriesResult,
  });

  if (alliances.length === 0) {
    return <></>;
  }

  return (
    <Card className="mt-12 bg-neutral-50/50 p-2 dark:bg-neutral-900/50">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Playoff Bracket</CardTitle>
        <BracketViewThroughSelect
          matches={matches}
          event={event}
          value={viewThrough}
          onValueChange={setViewThrough}
        />
      </CardHeader>

      <div className="overflow-x-auto overflow-y-hidden">
        <div ref={containerRef} className="relative isolate min-w-max px-4">
          <div className="relative z-1 space-y-4">
            {/* Upper Bracket */}
            <div className="space-y-4">
              <h2 className="text-center text-xl font-medium">Upper Bracket</h2>
              <div className="flex items-start gap-8">
                {/* Round 1 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center">Round 1</h3>
                  <div className="space-y-4">
                    <BracketMatch
                      ref={(node) => {
                        matchRefs.current['Match 1'] = node;
                      }}
                      matchLabel="Match 1"
                      isNext={nextLabel === 'Match 1'}
                      sides={sides['Match 1']}
                      alliances={alliances}
                      matches={matchesBySet[1]}
                      event={event}
                      hoveredAlliance={hoveredAlliance}
                      setHoveredAlliance={setHoveredAlliance}
                      getSeriesResult={getSeriesResult}
                      getAllianceDisplayName={getAllianceDisplayName}
                      showFullAlliance
                    />
                    <BracketMatch
                      ref={(node) => {
                        matchRefs.current['Match 2'] = node;
                      }}
                      matchLabel="Match 2"
                      isNext={nextLabel === 'Match 2'}
                      sides={sides['Match 2']}
                      alliances={alliances}
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
                      ref={(node) => {
                        matchRefs.current['Match 3'] = node;
                      }}
                      matchLabel="Match 3"
                      isNext={nextLabel === 'Match 3'}
                      sides={sides['Match 3']}
                      alliances={alliances}
                      matches={matchesBySet[3]}
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
                      ref={(node) => {
                        matchRefs.current.Finals = node;
                      }}
                      matchLabel="Finals"
                      isNext={nextLabel === 'Finals'}
                      sides={sides['Finals']}
                      alliances={alliances}
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
                {/* Round 2 - Lower */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center">Round 2</h3>
                  <div className="space-y-4">
                    <BracketMatch
                      ref={(node) => {
                        matchRefs.current['Match 4'] = node;
                      }}
                      matchLabel="Match 4"
                      isNext={nextLabel === 'Match 4'}
                      sides={sides['Match 4']}
                      alliances={alliances}
                      matches={matchesBySet[4]}
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
                      ref={(node) => {
                        matchRefs.current['Match 5'] = node;
                      }}
                      matchLabel="Match 5"
                      isNext={nextLabel === 'Match 5'}
                      sides={sides['Match 5']}
                      alliances={alliances}
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
