import { useQueries, useQuery } from '@tanstack/react-query';
import { createFileRoute, notFound } from '@tanstack/react-router';
import { useEffect, useRef, useState } from 'react';

import { type EventColors, getEventColors } from '~/api/colors';
import {
  AllianceColor,
  CompLevel,
  type Event,
  EventRanking,
  EventType,
  type Match,
  getDistrictHistory,
} from '~/api/tba/read';
import {
  getDistrictHistoryOptions,
  getDistrictTeamsKeysOptions,
  getEventMatchesOptions,
  getEventRankingsOptions,
  getEventsByYearOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { publicCacheControlHeaders } from '~/lib/utils';

const CURRENT_YEAR = 2026;
const REFETCH_INTERVAL = 60_000;

export const Route = createFileRoute(
  '/district/$districtAbbreviation/tracking',
)({
  loader: async ({ params }) => {
    const historyResult = await getDistrictHistory({
      path: { district_abbreviation: params.districtAbbreviation },
    });

    if (historyResult.data === undefined || historyResult.data.length === 0) {
      throw notFound();
    }

    const history = historyResult.data;
    const displayName = history[history.length - 1].display_name;

    return {
      abbreviation: params.districtAbbreviation,
      displayName,
    };
  },
  headers: publicCacheControlHeaders(),
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [
          { title: 'FIRST Championship Tracking - The Blue Alliance' },
          {
            name: 'description',
            content: 'Track district teams at the FIRST Championship.',
          },
        ],
      };
    }

    return {
      meta: [
        {
          title: `${loaderData.displayName} at FIRST Championship ${CURRENT_YEAR} - The Blue Alliance`,
        },
        {
          name: 'description',
          content: `Track ${loaderData.displayName} teams competing at the ${CURRENT_YEAR} FIRST Championship.`,
        },
      ],
    };
  },
  component: TrackingPage,
});

// --- Color helpers ---

function hexToRgb(hex: string): [number, number, number] | null {
  const cleaned = hex.replace('#', '');
  if (cleaned.length !== 6) return null;
  const r = parseInt(cleaned.slice(0, 2), 16);
  const g = parseInt(cleaned.slice(2, 4), 16);
  const b = parseInt(cleaned.slice(4, 6), 16);
  if (isNaN(r) || isNaN(g) || isNaN(b)) return null;
  return [r, g, b];
}

function getTextColor(hex: string): 'black' | 'white' {
  const rgb = hexToRgb(hex);
  if (!rgb) return 'white';
  const [r, g, b] = rgb;
  return (r * 299 + g * 587 + b * 114) / 1000 >= 128 ? 'black' : 'white';
}

function teamNumberFromKey(teamKey: string): string {
  return teamKey.replace('frc', '');
}

// --- Match label ---

function matchLabel(match: Match): string {
  if (match.comp_level === CompLevel.QM) {
    return `qm${match.match_number}`;
  }
  return `${match.comp_level}${match.set_number}-${match.match_number}`;
}

// Sort order for comp levels
const COMP_LEVEL_ORDER: Record<CompLevel, number> = {
  [CompLevel.QM]: 0,
  [CompLevel.EF]: 1,
  [CompLevel.QF]: 2,
  [CompLevel.SF]: 3,
  [CompLevel.F]: 4,
};

function sortMatches(matches: Match[]): Match[] {
  return [...matches].sort((a, b) => {
    const levelDiff =
      COMP_LEVEL_ORDER[a.comp_level] - COMP_LEVEL_ORDER[b.comp_level];
    if (levelDiff !== 0) return levelDiff;
    if (a.set_number !== b.set_number) return a.set_number - b.set_number;
    return a.match_number - b.match_number;
  });
}

// --- Types ---

type ColorsQueryResult =
  | { status: number; data: EventColors }
  | { status: 500 }
  | undefined;

// --- Team color helper ---

interface TeamCellColors {
  background: string;
  text: string;
  outline?: string;
}

function resolveTeamColors(
  teamKey: string,
  colors: ColorsQueryResult,
): TeamCellColors | null {
  if (colors === undefined || colors.status === 500 || !('data' in colors))
    return null;
  const tc = colors.data.teams[teamKey.substring(3)]?.colors;
  if (!tc) return null;
  const bg = tc.primaryHex.startsWith('#')
    ? tc.primaryHex
    : `#${tc.primaryHex}`;
  const textColor = getTextColor(bg);
  const secondary =
    tc.verified && tc.secondaryHex
      ? tc.secondaryHex.startsWith('#')
        ? tc.secondaryHex
        : `#${tc.secondaryHex}`
      : undefined;
  return { background: bg, text: textColor, outline: secondary };
}

// --- Team cell component ---

function TeamCell({
  teamKey,
  alliance,
  colors,
  districtTeamSet,
}: {
  teamKey: string;
  alliance: 'red' | 'blue';
  colors: ColorsQueryResult;
  districtTeamSet: Set<string>;
}) {
  const number = teamNumberFromKey(teamKey);
  const isDistrictTeam = districtTeamSet.has(teamKey);

  const teamColors = isDistrictTeam ? resolveTeamColors(teamKey, colors) : null;

  let cellColors: TeamCellColors;

  if (teamColors !== null) {
    cellColors = teamColors;
  } else {
    cellColors = { background: '', text: '' };
  }

  const allianceClass =
    alliance === 'red' ? 'bg-alliance-red-cell' : 'bg-alliance-blue-cell';

  const style: React.CSSProperties = cellColors.background
    ? {
        backgroundColor: cellColors.background,
        color: cellColors.text,
        ...(cellColors.outline
          ? {
              outline: `2px solid ${cellColors.outline}`,
              outlineOffset: '-2px',
            }
          : {}),
      }
    : {};

  return (
    <TableCell
      className={`px-2 py-1 text-center text-xs font-medium ${
        cellColors.background ? '' : allianceClass
      }`}
      style={style}
    >
      <div className={isDistrictTeam ? 'font-bold' : 'opacity-70'}>
        <a
          href={`https://www.thebluealliance.com/team/${number}`}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: cellColors.text }}
          className="hover:underline"
        >
          {number}
        </a>
      </div>
    </TableCell>
  );
}

// --- Matches table ---

function MatchesTable({
  matches,
  eventColors,
  districtTeamSet,
  divisionNames,
}: {
  matches: Match[];
  eventColors: Map<string, ColorsQueryResult>;
  districtTeamSet: Set<string>;
  divisionNames?: Map<string, string>;
}) {
  const sorted = sortMatches(matches);

  if (sorted.length === 0) {
    return (
      <p className="py-4 text-center text-sm text-muted-foreground">
        No matches yet.
      </p>
    );
  }

  return (
    <Table className="text-xs">
      <TableHeader>
        <TableRow>
          <TableHead className="text-center">Match</TableHead>
          {divisionNames && (
            <TableHead className="text-center">Division</TableHead>
          )}
          <TableHead className="text-center" colSpan={3}>
            Red Alliance
          </TableHead>
          <TableHead className="text-center">Red</TableHead>
          <TableHead className="text-center">Blue</TableHead>
          <TableHead className="text-center" colSpan={3}>
            Blue Alliance
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sorted.map((match) => {
          const colors = eventColors.get(match.event_key);
          const redTeams = match.alliances.red.team_keys;
          const blueTeams = match.alliances.blue.team_keys;
          const redScore = match.alliances.red.score;
          const blueScore = match.alliances.blue.score;
          const played = redScore >= 0;
          const winner = match.winning_alliance;

          return (
            <TableRow key={match.key}>
              <TableCell
                className="text-center font-mono text-xs text-muted-foreground"
              >
                <a
                  href={`https://www.thebluealliance.com/match/${match.key}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                >
                  {matchLabel(match)}
                </a>
              </TableCell>
              {divisionNames && (
                <TableCell className="text-center text-muted-foreground">
                  {divisionNames.get(match.event_key) ?? ''}
                </TableCell>
              )}
              {redTeams.slice(0, 3).map((tk) => (
                <TeamCell
                  key={tk}
                  teamKey={tk}
                  alliance="red"
                  colors={colors}
                  districtTeamSet={districtTeamSet}
                />
              ))}
              {/* Pad if fewer than 3 */}
              {Array.from({ length: Math.max(0, 3 - redTeams.length) }).map(
                (_, i) => (
                  <TableCell key={`red-pad-${i}`} />
                ),
              )}
              <TableCell
                className={`text-center font-bold ${
                  winner === AllianceColor.RED
                    ? 'bg-alliance-red-cell-winner'
                    : 'bg-alliance-red-cell'
                }`}
              >
                {played ? redScore : '—'}
              </TableCell>
              <TableCell
                className={`text-center font-bold ${
                  winner === AllianceColor.BLUE
                    ? 'bg-alliance-blue-cell-winner'
                    : 'bg-alliance-blue-cell'
                }`}
              >
                {played ? blueScore : '—'}
              </TableCell>
              {blueTeams.slice(0, 3).map((tk) => (
                <TeamCell
                  key={tk}
                  teamKey={tk}
                  alliance="blue"
                  colors={colors}
                  districtTeamSet={districtTeamSet}
                />
              ))}
              {Array.from({ length: Math.max(0, 3 - blueTeams.length) }).map(
                (_, i) => (
                  <TableCell key={`blue-pad-${i}`} />
                ),
              )}
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

// --- Rankings table ---

function RankingsTable({
  rankings,
  districtTeamSet,
}: {
  rankings: EventRanking | null | undefined;
  districtTeamSet: Set<string>;
}) {
  if (!rankings?.rankings || rankings.rankings.length === 0) {
    return (
      <p className="py-4 text-center text-sm text-muted-foreground">
        No rankings available.
      </p>
    );
  }

  const filtered = rankings.rankings.filter((r) =>
    districtTeamSet.has(r.team_key),
  );

  if (filtered.length === 0) {
    return (
      <p className="py-4 text-center text-sm text-muted-foreground">
        No district teams in rankings yet.
      </p>
    );
  }

  return (
    <Table className="text-xs">
      <TableHeader>
        <TableRow>
          <TableHead className="text-center">Rank</TableHead>
          <TableHead className="text-center">Team</TableHead>
          <TableHead className="text-center">W-L-T</TableHead>
          <TableHead className="text-center">Matches</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {filtered.map((r) => {
          const number = teamNumberFromKey(r.team_key);
          const record = r.record;
          return (
            <TableRow key={r.team_key}>
              <TableCell className="text-center font-bold">{r.rank}</TableCell>
              <TableCell className="text-center">
                <a
                  href={`https://www.thebluealliance.com/team/${number}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                >
                  {number}
                </a>
              </TableCell>
              <TableCell className="text-center">
                {record
                  ? `${record.wins}-${record.losses}-${record.ties}`
                  : '—'}
              </TableCell>
              <TableCell className="text-center">{r.matches_played}</TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

// --- All Rankings table (across all divisions) ---

function AllRankingsTable({
  divisions,
  districtTeamSet,
}: {
  divisions: Array<{
    name: string;
    rankings: EventRanking | null | undefined;
    eventKey: string;
  }>;
  districtTeamSet: Set<string>;
}) {
  type Row = {
    rank: number;
    teamKey: string;
    division: string;
    eventKey: string;
    wins: number;
    losses: number;
    ties: number;
    matchesPlayed: number;
  };

  const rows: Row[] = divisions.flatMap(({ name, rankings, eventKey }) => {
    if (!rankings?.rankings) return [];
    return rankings.rankings
      .filter((r) => districtTeamSet.has(r.team_key))
      .map((r) => ({
        rank: r.rank,
        teamKey: r.team_key,
        division: name,
        eventKey,
        wins: r.record?.wins ?? 0,
        losses: r.record?.losses ?? 0,
        ties: r.record?.ties ?? 0,
        matchesPlayed: r.matches_played,
      }));
  });

  if (rows.length === 0) {
    return (
      <p className="py-4 text-center text-sm text-muted-foreground">
        No rankings available yet.
      </p>
    );
  }

  // Sort by rank, then by division name as a tiebreaker
  rows.sort((a, b) =>
    a.rank !== b.rank ? a.rank - b.rank : a.division.localeCompare(b.division),
  );

  return (
    <Table className="text-xs">
      <TableHeader>
        <TableRow>
          <TableHead className="w-1/5 text-center">Rank</TableHead>
          <TableHead className="w-1/5 text-center">Team</TableHead>
          <TableHead className="w-1/5 text-center">Division</TableHead>
          <TableHead className="w-1/5 text-center">W-L-T</TableHead>
          <TableHead className="w-1/5 text-center">Matches</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((r) => {
          const number = teamNumberFromKey(r.teamKey);
          return (
            <TableRow key={r.teamKey}>
              <TableCell className="text-center font-bold">{r.rank}</TableCell>
              <TableCell className="text-center">
                <a
                  href={`https://www.thebluealliance.com/team/${number}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                >
                  {number}
                </a>
              </TableCell>
              <TableCell className="text-center">{r.division}</TableCell>
              <TableCell className="text-center">
                {`${r.wins}-${r.losses}-${r.ties}`}
              </TableCell>
              <TableCell className="text-center">{r.matchesPlayed}</TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

// --- Main page component ---

function TrackingPage() {
  const { abbreviation, displayName } = Route.useLoaderData();
  const [year, setYear] = useState(CURRENT_YEAR);
  const districtKey = `${year}${abbreviation}`;

  // Fetch district history to know which years this district existed
  const districtHistoryQuery = useQuery({
    ...getDistrictHistoryOptions({
      path: { district_abbreviation: abbreviation },
    }),
  });

  const validYears: number[] = districtHistoryQuery.data
    ? districtHistoryQuery.data
        .map((d) => d.year)
        .filter((y) => y <= CURRENT_YEAR)
        .sort((a, b) => b - a)
    : [CURRENT_YEAR];

  // Snap year to most recent valid year once history loads
  useEffect(() => {
    if (districtHistoryQuery.data && !validYears.includes(year)) {
      setYear(validYears[0] ?? CURRENT_YEAR);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [districtHistoryQuery.data]);

  // Auto-refresh countdown
  const [countdown, setCountdown] = useState(REFETCH_INTERVAL / 1000);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startCountdown = () => {
    if (countdownRef.current) clearInterval(countdownRef.current);
    setCountdown(REFETCH_INTERVAL / 1000);
    countdownRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          return REFETCH_INTERVAL / 1000;
        }
        return prev - 1;
      });
    }, 1000);
  };

  useEffect(() => {
    startCountdown();
    return () => {
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, []);

  // Fetch district team keys
  const districtTeamsQuery = useQuery({
    ...getDistrictTeamsKeysOptions({ path: { district_key: districtKey } }),
    refetchInterval: REFETCH_INTERVAL,
  });

  // Fetch all events for the year and filter to CMP divisions
  const allEventsQuery = useQuery({
    ...getEventsByYearOptions({ path: { year } }),
    refetchInterval: REFETCH_INTERVAL,
  });

  const cmpDivisions: Event[] = (allEventsQuery.data ?? []).filter(
    (e) => e.event_type === EventType.CMP_DIVISION,
  );

  const districtTeamSet = new Set<string>(districtTeamsQuery.data ?? []);

  // Per-division queries: matches, rankings, colors
  const matchesQueries = useQueries({
    queries: cmpDivisions.map((div) => ({
      ...getEventMatchesOptions({ path: { event_key: div.key } }),
      refetchInterval: REFETCH_INTERVAL,
    })),
  });

  const rankingsQueries = useQueries({
    queries: cmpDivisions.map((div) => ({
      ...getEventRankingsOptions({ path: { event_key: div.key } }),
      refetchInterval: REFETCH_INTERVAL,
    })),
  });

  const colorsQueries = useQueries({
    queries: cmpDivisions.map((div) => ({
      queryKey: ['eventColors', div.key],
      queryFn: () => getEventColors({ eventKey: div.key }),
      refetchInterval: REFETCH_INTERVAL,
    })),
  });

  // Reset countdown when any query finishes refetching
  const isFetchingAny =
    districtTeamsQuery.isFetching ||
    allEventsQuery.isFetching ||
    matchesQueries.some((q) => q.isFetching) ||
    rankingsQueries.some((q) => q.isFetching);

  const prevFetchingRef = useRef(false);
  useEffect(() => {
    if (prevFetchingRef.current && !isFetchingAny) {
      startCountdown();
    }
    prevFetchingRef.current = isFetchingAny;
  }, [isFetchingAny]);

  // Build a map from eventKey -> colors query result
  const eventColorsMap = new Map<string, ColorsQueryResult>();
  cmpDivisions.forEach((div, idx) => {
    const colorsData = colorsQueries[idx]?.data;
    eventColorsMap.set(div.key, colorsData);
  });

  // Matches filtered to only those involving district teams
  function filterMatchesToDistrictTeams(matches: Match[]): Match[] {
    return matches.filter((m) => {
      const allTeams = [
        ...m.alliances.red.team_keys,
        ...m.alliances.blue.team_keys,
      ];
      return allTeams.some((tk) => districtTeamSet.has(tk));
    });
  }

  const allMatches: Match[] = cmpDivisions.flatMap((_, idx) => {
    const data = matchesQueries[idx]?.data;
    return data ? filterMatchesToDistrictTeams(data) : [];
  });

  const isLoading = allEventsQuery.isPending || districtTeamsQuery.isPending;

  const divisionTabIds = cmpDivisions.map((div) => div.short_name ?? div.name);
  const defaultTab = 'all-rankings';

  return (
    <div>
      <div className="mt-4 flex items-center justify-between gap-4">
        <h1 className="text-4xl font-medium">
          {displayName} at FIRST Championship {year}
        </h1>
        <div className="flex items-center gap-2">
          <span
            className="rounded border px-2 py-1 text-xs text-muted-foreground"
          >
            {isFetchingAny ? 'Refreshing…' : `Auto-refresh in ${countdown}s`}
          </span>
          <Select
            value={String(year)}
            onValueChange={(v) => setYear(Number(v))}
          >
            <SelectTrigger className="w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {validYears.map((y) => (
                <SelectItem key={y} value={String(y)}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Tabs defaultValue={defaultTab} className="mt-4">
        <TabsList
          className="flex h-auto flex-wrap items-center justify-evenly
            *:basis-1/2 lg:*:basis-1"
        >
          <TabsTrigger value="all-rankings">Rankings</TabsTrigger>
          {cmpDivisions.map((div, idx) => (
            <TabsTrigger key={div.key} value={divisionTabIds[idx]}>
              {div.short_name ?? div.name}
            </TabsTrigger>
          ))}
          <TabsTrigger value="all-matches">All Matches</TabsTrigger>
        </TabsList>

        {isLoading && (
          <p className="mt-4 text-sm text-muted-foreground">
            Loading divisions…
          </p>
        )}

        {!isLoading && cmpDivisions.length === 0 && (
          <p className="mt-4 text-sm text-muted-foreground">
            No FIRST Championship divisions found for {year}.
          </p>
        )}

        <TabsContent value="all-rankings">
          <Card>
            <CardHeader>
              <CardTitle>All Rankings</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <AllRankingsTable
                divisions={cmpDivisions.map((div, idx) => ({
                  name: div.short_name ?? div.name,
                  rankings: rankingsQueries[idx]?.data ?? null,
                  eventKey: div.key,
                }))}
                districtTeamSet={districtTeamSet}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {cmpDivisions.map((div, idx) => {
          const divMatches = matchesQueries[idx]?.data
            ? filterMatchesToDistrictTeams(matchesQueries[idx].data ?? [])
            : [];
          const divRankings = rankingsQueries[idx]?.data ?? null;

          return (
            <TabsContent key={div.key} value={divisionTabIds[idx]}>
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Rankings</CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <RankingsTable
                      rankings={divRankings}
                      districtTeamSet={districtTeamSet}
                    />
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Matches</CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <MatchesTable
                      matches={divMatches}
                      eventColors={eventColorsMap}
                      districtTeamSet={districtTeamSet}
                    />
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          );
        })}

        <TabsContent value="all-matches">
          <Card>
            <CardHeader>
              <CardTitle>All Matches</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <MatchesTable
                matches={allMatches}
                eventColors={eventColorsMap}
                districtTeamSet={districtTeamSet}
                divisionNames={
                  new Map(
                    cmpDivisions.map((div) => [
                      div.key,
                      div.short_name ?? div.name,
                    ]),
                  )
                }
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
