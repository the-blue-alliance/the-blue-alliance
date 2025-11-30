import { maxBy, startCase, uniq } from 'lodash-es';
import { useMemo, useState } from 'react';

import { Event, Match } from '~/api/tba/read';
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
import {
  calculateTeamRecordsFromMatches,
  getAllianceMatchResult,
  getMatchScoreWithoutAdjustPoints,
} from '~/lib/matchUtils';
import { addRecords, cn, joinComponents, winrateFromRecord } from '~/lib/utils';

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

      <div className="flex items-center justify-end gap-2">
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

      <div className="grid gap-6 lg:grid-cols-3">
        <SingleHighlightedMatchPerYearTable
          teamKey={teamKey}
          matchByYear={highScoresByYear}
          title="High Scores by Year"
        />
        <SingleHighlightedMatchPerYearTable
          teamKey={teamKey}
          matchByYear={blowoutWinsByYear}
          title="Biggest Win Margins by Year"
        />
        <SingleHighlightedMatchPerYearTable
          teamKey={teamKey}
          matchByYear={blowoutLossesByYear}
          title="Biggest Loss Margins by Year"
        />
      </div>
    </div>
  );
}
