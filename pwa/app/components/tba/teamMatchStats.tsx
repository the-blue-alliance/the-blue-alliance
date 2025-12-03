import { maxBy, startCase, uniq } from 'lodash-es';
import { ReactNode, useMemo, useState } from 'react';

import { Event, Match, WltRecord } from '~/api/tba/read';
import { TitledCard } from '~/components/tba/cards';
import { TeamLink } from '~/components/tba/links';
import { Checkbox } from '~/components/ui/checkbox';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import {
  calculateTeamRecordsFromMatches,
  getAllianceMatchResult,
  getMatchScoreWithoutAdjustPoints,
} from '~/lib/matchUtils';
import {
  addRecords,
  cn,
  confidence,
  joinComponents,
  stringifyRecord,
  winrateFromRecord,
} from '~/lib/utils';

const NUM_OTHER_TEAMS_TO_SHOW = 25;

interface TeamRecord extends WltRecord {
  team: string;
  count: number;
}

interface TeamStatsTableProps {
  title: string;
  data: TeamRecord[];
  valueColumnHeader: ReactNode;
  getValue: (item: TeamRecord) => string | number;
  limit?: number;
}

function TeamStatsTable({
  title,
  data,
  valueColumnHeader,
  getValue,
  limit = NUM_OTHER_TEAMS_TO_SHOW,
}: TeamStatsTableProps) {
  return (
    <div className="rounded-lg border bg-card">
      <div className="border-b px-6 py-4">
        <h3 className="text-lg font-semibold">{title}</h3>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Team</TableHead>
            <TableHead className="text-right">Record</TableHead>
            <TableHead className="text-right">{valueColumnHeader}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.slice(0, limit).map((record) => (
            <TableRow key={record.team}>
              <TableCell>
                <TeamLink teamOrKey={record.team}>
                  <span className="font-medium">
                    {record.team.substring(3)}
                  </span>
                </TeamLink>
              </TableCell>
              <TableCell className="text-right text-sm text-muted-foreground">
                {stringifyRecord(record)}
              </TableCell>
              <TableCell className="text-right font-semibold">
                {getValue(record)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function recordsToSortedList(
  records: Record<string, WltRecord & { count: number }>,
  sortFn: (a: TeamRecord, b: TeamRecord) => number,
): TeamRecord[] {
  return Object.entries(records)
    .map(([team, stats]) => ({ team, ...stats }))
    .sort(sortFn);
}

interface TeamMatchStatsProps {
  teamKey: string;
  matches: Match[];
  events: Event[];
}

interface Streak {
  type: 'win' | 'loss' | 'tie';
  count: number;
  firstMatch: Match | undefined;
  lastMatch: Match | undefined;
}

function calculateStreaks(teamKey: string, matches: Match[]): Streak[] {
  let currentStreak: Streak = {
    type: 'tie',
    count: 0,
    firstMatch: undefined,
    lastMatch: undefined,
  };
  const streaks: Streak[] = [];

  for (let i = 0; i < matches.length; i++) {
    const isRed = matches[i].alliances.red.team_keys.includes(teamKey);

    const result = getAllianceMatchResult(
      matches[i],
      isRed ? 'red' : 'blue',
      'score-based',
    );

    if (result === undefined) {
      continue;
    }

    if (currentStreak.type === result) {
      currentStreak.count++;
      currentStreak.lastMatch = matches[i];
    } else {
      if (currentStreak.count > 0) {
        streaks.push(currentStreak);
      }
      currentStreak = {
        type: result,
        count: 1,
        firstMatch: matches[i],
        lastMatch: matches[i],
      };
    }
  }

  streaks.push(currentStreak);

  return streaks;
}

function groupMatchesByYear(matches: Match[]) {
  return matches.reduce(
    (acc, match) => {
      const year = Number(match.event_key.slice(0, 4));
      return {
        ...acc,
        [year]: [...(acc[year] ?? []), match],
      };
    },
    {} as Record<number, Match[]>,
  );
}

interface YearStatTableProps {
  teamKey: string;
  matchByYear: Record<number, Match | undefined>;
  title: string;
}

function SingleHighlightedMatchPerYearTable({
  teamKey,
  matchByYear,
  title,
}: YearStatTableProps) {
  return (
    <div className="rounded-lg border bg-card">
      <div className="border-b px-6 py-4">
        <h3 className="text-lg font-semibold">{title}</h3>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Year / Match</TableHead>
            <TableHead>Score</TableHead>
            <TableHead>Alliances</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Object.entries(matchByYear)
            .sort((a, b) => Number(b[0]) - Number(a[0]))
            .map(
              ([year, match]) =>
                match && (
                  <TableRow key={match.key}>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium">{year}</span>
                        <span className="text-xs text-muted-foreground">
                          {match.key}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span
                          className={cn({
                            'font-semibold':
                              match.alliances.red.team_keys.includes(teamKey),
                            'text-muted-foreground':
                              !match.alliances.red.team_keys.includes(teamKey),
                          })}
                        >
                          {match.alliances.red.score}
                        </span>
                        <span
                          className={cn({
                            'font-semibold':
                              match.alliances.blue.team_keys.includes(teamKey),
                            'text-muted-foreground':
                              !match.alliances.blue.team_keys.includes(teamKey),
                          })}
                        >
                          {match.alliances.blue.score}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col text-sm">
                        <span
                          className={cn({
                            'text-muted-foreground':
                              !match.alliances.red.team_keys.includes(teamKey),
                          })}
                        >
                          {joinComponents(
                            match.alliances.red.team_keys.map((key) => (
                              <TeamLink
                                key={key}
                                teamOrKey={key}
                                year={Number(year)}
                              >
                                <span
                                  className={cn({
                                    'font-semibold': key === teamKey,
                                  })}
                                >
                                  {key.substring(3)}
                                </span>
                              </TeamLink>
                            )),
                            ' - ',
                          )}
                        </span>
                        <span
                          className={cn({
                            'text-muted-foreground':
                              !match.alliances.blue.team_keys.includes(teamKey),
                          })}
                        >
                          {joinComponents(
                            match.alliances.blue.team_keys.map((key) => (
                              <TeamLink
                                key={key}
                                teamOrKey={key}
                                year={Number(year)}
                              >
                                <span
                                  className={cn({
                                    'font-semibold': key === teamKey,
                                  })}
                                >
                                  {key.substring(3)}
                                </span>
                              </TeamLink>
                            )),
                            ' - ',
                          )}
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                ),
            )}
        </TableBody>
      </Table>
    </div>
  );
}

export default function TeamMatchStats({
  teamKey,
  matches,
  events,
}: TeamMatchStatsProps) {
  const [
    useOriginalScoreForPlayoffRedCards,
    setUseOriginalScoreForPlayoffRedCards,
  ] = useState(true);

  const uniqueTeamsSeen = uniq(
    matches.flatMap((m) => [
      ...m.alliances.red.team_keys,
      ...m.alliances.blue.team_keys,
    ]),
  ).filter((key) => key !== teamKey);

  const recordsWith = useMemo(() => {
    const records: Record<string, WltRecord & { count: number }> = {};

    for (const match of matches) {
      const isRed = match.alliances.red.team_keys.includes(teamKey);
      const alliance = isRed ? match.alliances.red : match.alliances.blue;
      const result = getAllianceMatchResult(
        match,
        isRed ? 'red' : 'blue',
        'score-based',
      );

      for (const teammate of alliance.team_keys) {
        if (teammate !== teamKey) {
          if (!records[teammate]) {
            records[teammate] = { count: 0, wins: 0, losses: 0, ties: 0 };
          }
          records[teammate].count++;
          if (result === 'win') records[teammate].wins++;
          else if (result === 'loss') records[teammate].losses++;
          else if (result === 'tie') records[teammate].ties++;
        }
      }
    }

    return records;
  }, [matches, teamKey]);

  const recordsAgainst = useMemo(() => {
    const records: Record<string, WltRecord & { count: number }> = {};

    for (const match of matches) {
      const isRed = match.alliances.red.team_keys.includes(teamKey);
      const opposingAlliance = isRed
        ? match.alliances.blue
        : match.alliances.red;
      const result = getAllianceMatchResult(
        match,
        isRed ? 'red' : 'blue',
        'score-based',
      );

      for (const opponent of opposingAlliance.team_keys) {
        if (!records[opponent]) {
          records[opponent] = { count: 0, wins: 0, losses: 0, ties: 0 };
        }
        records[opponent].count++;
        if (result === 'win') records[opponent].wins++;
        else if (result === 'loss') records[opponent].losses++;
        else if (result === 'tie') records[opponent].ties++;
      }
    }

    return records;
  }, [matches, teamKey]);

  const withStats = useMemo(
    () => ({
      mostPlayed: recordsToSortedList(recordsWith, (a, b) => b.count - a.count),
      mostWins: recordsToSortedList(recordsWith, (a, b) => b.wins - a.wins),
      mostLosses: recordsToSortedList(
        recordsWith,
        (a, b) => b.losses - a.losses,
      ),
      bestRecord: recordsToSortedList(
        recordsWith,
        (a, b) => confidence(b.wins, b.losses) - confidence(a.wins, a.losses),
      ),
      worstRecord: recordsToSortedList(
        recordsWith,
        (a, b) => confidence(b.losses, b.wins) - confidence(a.losses, a.wins),
      ),
    }),
    [recordsWith],
  );

  const againstStats = useMemo(
    () => ({
      mostPlayed: recordsToSortedList(
        recordsAgainst,
        (a, b) => b.count - a.count,
      ),
      mostWins: recordsToSortedList(recordsAgainst, (a, b) => b.wins - a.wins),
      mostLosses: recordsToSortedList(
        recordsAgainst,
        (a, b) => b.losses - a.losses,
      ),
      bestRecord: recordsToSortedList(
        recordsAgainst,
        (a, b) => confidence(b.wins, b.losses) - confidence(a.wins, a.losses),
      ),
      worstRecord: recordsToSortedList(
        recordsAgainst,
        (a, b) => confidence(b.losses, b.wins) - confidence(a.losses, a.wins),
      ),
    }),
    [recordsAgainst],
  );

  const highScoresByYear: Record<number, Match | undefined> = useMemo(() => {
    return Object.fromEntries(
      Object.entries(groupMatchesByYear(matches)).map(([year, matches]) => {
        return [
          Number(year),
          maxBy(matches, (m) =>
            m.alliances.red.team_keys.includes(teamKey)
              ? m.alliances.red.score
              : m.alliances.blue.score,
          ),
        ];
      }),
    );
  }, [matches, teamKey]);

  const blowoutWinsByYear: Record<number, Match | undefined> = useMemo(() => {
    return Object.fromEntries(
      Object.entries(groupMatchesByYear(matches)).map(([year, matches]) => {
        return [
          Number(year),
          maxBy(matches, (m) => {
            const originalScore = getMatchScoreWithoutAdjustPoints(m);
            const redScore =
              useOriginalScoreForPlayoffRedCards && m.comp_level != 'qm'
                ? originalScore.redScore
                : m.alliances.red.score;
            const blueScore =
              useOriginalScoreForPlayoffRedCards && m.comp_level != 'qm'
                ? originalScore.blueScore
                : m.alliances.blue.score;
            return m.alliances.red.team_keys.includes(teamKey)
              ? redScore - blueScore
              : blueScore - redScore;
          }),
        ];
      }),
    );
  }, [matches, teamKey, useOriginalScoreForPlayoffRedCards]);

  const blowoutLossesByYear: Record<number, Match | undefined> = useMemo(() => {
    return Object.fromEntries(
      Object.entries(groupMatchesByYear(matches)).map(([year, matches]) => {
        return [
          Number(year),
          maxBy(matches, (m) => {
            const originalScore = getMatchScoreWithoutAdjustPoints(m);
            const redScore =
              useOriginalScoreForPlayoffRedCards && m.comp_level != 'qm'
                ? originalScore.redScore
                : m.alliances.red.score;
            const blueScore =
              useOriginalScoreForPlayoffRedCards && m.comp_level != 'qm'
                ? originalScore.blueScore
                : m.alliances.blue.score;
            return m.alliances.blue.team_keys.includes(teamKey)
              ? redScore - blueScore
              : blueScore - redScore;
          }),
        ];
      }),
    );
  }, [matches, teamKey, useOriginalScoreForPlayoffRedCards]);

  const records = useMemo(
    () => calculateTeamRecordsFromMatches(teamKey, matches, 'score-based'),
    [teamKey, matches],
  );

  const qualsRecord = records.quals;
  const playoffRecord = records.playoff;
  const overallRecord = addRecords(qualsRecord, playoffRecord);

  const streaks = useMemo(() => {
    return calculateStreaks(teamKey, matches);
  }, [matches, teamKey]);

  const currentStreak = streaks[streaks.length - 1];
  const longestWinStreak = maxBy(streaks, (s) =>
    s.type === 'win' ? s.count : 0,
  ) ?? { type: 'win', count: 0, firstMatch: undefined, lastMatch: undefined };
  const longestLossStreak = maxBy(streaks, (s) =>
    s.type === 'loss' ? s.count : 0,
  ) ?? { type: 'loss', count: 0, firstMatch: undefined, lastMatch: undefined };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        <TitledCard
          cardTitle={`${(winrateFromRecord(qualsRecord) * 100).toFixed(1)}%`}
          cardSubtitle={
            <span>
              Qual Winrate
              <br />
              <span className="text-sm">
                {qualsRecord.wins}-{qualsRecord.losses}-{qualsRecord.ties}
              </span>
            </span>
          }
        />
        <TitledCard
          cardTitle={`${(winrateFromRecord(playoffRecord) * 100).toFixed(1)}%`}
          cardSubtitle={
            <span>
              Playoff Winrate
              <br />
              <span className="text-sm">
                {playoffRecord.wins}-{playoffRecord.losses}-{playoffRecord.ties}
              </span>
            </span>
          }
        />
        <TitledCard
          cardTitle={`${(winrateFromRecord(overallRecord) * 100).toFixed(1)}%`}
          cardSubtitle={
            <span>
              Overall Winrate
              <br />
              <span className="text-sm">
                {overallRecord.wins}-{overallRecord.losses}-{overallRecord.ties}
              </span>
            </span>
          }
        />
        <TitledCard cardTitle={events.length} cardSubtitle="Total Events" />
        <TitledCard cardTitle={matches.length} cardSubtitle="Total Matches" />
        <TitledCard
          cardTitle={uniqueTeamsSeen.length}
          cardSubtitle="Unique Teams Seen"
        />
        <TitledCard
          cardTitle={`${currentStreak.count}`}
          cardSubtitle={
            <span>
              Current {startCase(currentStreak.type)} Streak
              <br />
              <span className="text-sm">
                {currentStreak.firstMatch?.key} → {currentStreak.lastMatch?.key}
              </span>
            </span>
          }
        />
        <TitledCard
          cardTitle={`${longestWinStreak.count}`}
          cardSubtitle={
            <span>
              Longest Win Streak
              <br />
              <span className="text-sm">
                {longestWinStreak.firstMatch?.key} →{' '}
                {longestWinStreak.lastMatch?.key}
              </span>
            </span>
          }
        />
        <TitledCard
          cardTitle={`${longestLossStreak.count}`}
          cardSubtitle={
            <span>
              Longest Loss Streak
              <br />
              <span className="text-sm">
                {longestLossStreak.firstMatch?.key} →{' '}
                {longestLossStreak.lastMatch?.key}
              </span>
            </span>
          }
        />
      </div>

      <div className="flex items-center justify-start gap-2">
        <Checkbox
          id="exclude-red-cards"
          checked={useOriginalScoreForPlayoffRedCards}
          onCheckedChange={(checked) =>
            setUseOriginalScoreForPlayoffRedCards(checked === true)
          }
        />
        <label
          htmlFor="exclude-red-cards"
          className="cursor-pointer text-sm leading-none font-medium
            peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        >
          Use Original Score for Playoff Red Cards
        </label>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Tabs defaultValue="high-scores" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="high-scores">High Scores</TabsTrigger>
            <TabsTrigger value="biggest-wins">Biggest Wins</TabsTrigger>
            <TabsTrigger value="biggest-losses">Biggest Losses</TabsTrigger>
          </TabsList>
          <TabsContent value="high-scores">
            <SingleHighlightedMatchPerYearTable
              teamKey={teamKey}
              matchByYear={highScoresByYear}
              title="High Scores by Year"
            />
          </TabsContent>
          <TabsContent value="biggest-wins">
            <SingleHighlightedMatchPerYearTable
              teamKey={teamKey}
              matchByYear={blowoutWinsByYear}
              title="Biggest Win Margins by Year"
            />
          </TabsContent>
          <TabsContent value="biggest-losses">
            <SingleHighlightedMatchPerYearTable
              teamKey={teamKey}
              matchByYear={blowoutLossesByYear}
              title="Biggest Loss Margins by Year"
            />
          </TabsContent>
        </Tabs>

        <Tabs defaultValue="with" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="with">With</TabsTrigger>
            <TabsTrigger value="against">Against</TabsTrigger>
          </TabsList>
          <TabsContent value="with">
            <Tabs defaultValue="most-played" className="w-full">
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="most-played">Most Played</TabsTrigger>
                <TabsTrigger value="most-wins">Most Wins</TabsTrigger>
                <TabsTrigger value="most-losses">Most Losses</TabsTrigger>
                <TabsTrigger value="best-record">Best Record</TabsTrigger>
                <TabsTrigger value="worst-record">Worst Record</TabsTrigger>
              </TabsList>
              <TabsContent value="most-played">
                <TeamStatsTable
                  title="Most Played With"
                  data={withStats.mostPlayed}
                  valueColumnHeader="Matches Together"
                  getValue={(r) => r.count}
                />
              </TabsContent>
              <TabsContent value="most-wins">
                <TeamStatsTable
                  title="Most Wins With"
                  data={withStats.mostWins}
                  valueColumnHeader="Wins Together"
                  getValue={(r) => r.wins}
                  limit={20}
                />
              </TabsContent>
              <TabsContent value="most-losses">
                <TeamStatsTable
                  title="Most Losses With"
                  data={withStats.mostLosses}
                  valueColumnHeader="Losses Together"
                  getValue={(r) => r.losses}
                />
              </TabsContent>
              <TabsContent value="best-record">
                <TeamStatsTable
                  title="Best Record With"
                  data={withStats.bestRecord}
                  valueColumnHeader="Confidence"
                  getValue={(r) => confidence(r.wins, r.losses).toFixed(2)}
                />
              </TabsContent>
              <TabsContent value="worst-record">
                <TeamStatsTable
                  title="Worst Record With"
                  data={withStats.worstRecord}
                  valueColumnHeader="Confidence"
                  getValue={(r) => confidence(r.losses, r.wins).toFixed(2)}
                />
              </TabsContent>
            </Tabs>
          </TabsContent>
          <TabsContent value="against">
            <Tabs defaultValue="most-played" className="w-full">
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="most-played">Most Played</TabsTrigger>
                <TabsTrigger value="most-wins">Most Wins</TabsTrigger>
                <TabsTrigger value="most-losses">Most Losses</TabsTrigger>
                <TabsTrigger value="best-record">Best Record</TabsTrigger>
                <TabsTrigger value="worst-record">Worst Record</TabsTrigger>
              </TabsList>
              <TabsContent value="most-played">
                <TeamStatsTable
                  title="Most Played Against"
                  data={againstStats.mostPlayed}
                  valueColumnHeader="Matches Against"
                  getValue={(r) => r.count}
                />
              </TabsContent>
              <TabsContent value="most-wins">
                <TeamStatsTable
                  title="Most Wins Against"
                  data={againstStats.mostWins}
                  valueColumnHeader="Wins Against"
                  getValue={(r) => r.wins}
                  limit={20}
                />
              </TabsContent>
              <TabsContent value="most-losses">
                <TeamStatsTable
                  title="Most Losses Against"
                  data={againstStats.mostLosses}
                  valueColumnHeader="Losses Against"
                  getValue={(r) => r.losses}
                  limit={20}
                />
              </TabsContent>
              <TabsContent value="best-record">
                <TeamStatsTable
                  title="Best Record Against"
                  data={againstStats.bestRecord}
                  valueColumnHeader="Confidence"
                  getValue={(r) => confidence(r.wins, r.losses).toFixed(2)}
                  limit={20}
                />
              </TabsContent>
              <TabsContent value="worst-record">
                <TeamStatsTable
                  title="Worst Record Against"
                  data={againstStats.worstRecord}
                  valueColumnHeader="Confidence"
                  getValue={(r) => confidence(r.losses, r.wins).toFixed(2)}
                />
              </TabsContent>
            </Tabs>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
