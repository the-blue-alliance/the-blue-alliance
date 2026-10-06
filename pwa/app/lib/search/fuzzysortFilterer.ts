import fuzzysort from 'fuzzysort';
import { Temporal } from 'temporal-polyfill';

import { SearchIndex } from '~/api/tba/read';

type SearchableTeam = SearchIndex['teams'][number];
type SearchableEvent = SearchIndex['events'][number];

export interface SearchResult {
  type: 'team' | 'event';
  key: string;
  label: string;
  path: string;
}

interface ScoredResult {
  result: SearchResult;
  score: number;
}

const RESULT_LIMIT = 10;
const TEAM_NUMBER_PATTERN = /^(?:frc)?(\d+)$/i;
const TEAM_YEAR_PATTERN = /^(?:frc)?(\d+)[\s/]+(\d{4})$/i;

function teamResult(team: SearchableTeam, year?: number): SearchResult {
  const teamNumber = team.key.substring(3);
  const label = `${teamNumber} - ${team.nickname}`;
  const path = `/team/${teamNumber}`;
  return year === undefined
    ? { type: 'team', key: team.key, label, path }
    : {
        type: 'team',
        key: team.key,
        label: `${label} (${year})`,
        path: `${path}/${year}`,
      };
}

function eventResult(event: SearchableEvent): SearchResult {
  return {
    type: 'event',
    key: event.key,
    label: `${event.key.substring(0, 4)} ${event.name} [${event.key.substring(4)}]`,
    path: `/event/${event.key}`,
  };
}

function findTeamYear(
  teams: SearchableTeam[],
  query: string,
): SearchResult | undefined {
  const match = TEAM_YEAR_PATTERN.exec(query.trim());
  if (!match) {
    return undefined;
  }
  const [, teamNumber, year] = match;
  const team = teams.find((t) => t.key === `frc${Number(teamNumber)}`);
  return team && teamResult(team, Number(year));
}

function searchTeams(teams: SearchableTeam[], query: string): ScoredResult[] {
  const exactKey = `frc${TEAM_NUMBER_PATTERN.exec(query.trim())?.[1]}`;
  const results = fuzzysort.go(
    query,
    teams.map((t) => ({ ...t, team_number: Number(t.key.substring(3)) })),
    {
      limit: RESULT_LIMIT,
      keys: ['key', 'nickname', 'team_number'],
      threshold: 0.5,
    },
  );

  return results.map((r) => ({
    result: teamResult(r.obj),
    score: r.obj.key === exactKey ? Infinity : r.score,
  }));
}

function searchEvents(
  events: SearchableEvent[],
  query: string,
): ScoredResult[] {
  const results = fuzzysort.go(query, events, {
    limit: RESULT_LIMIT,
    keys: ['key', 'name'],
    threshold: 0.5,
    scoreFn: (r) => {
      // For current_year events, return score * 2
      // For current_year-1 events, return score * (2 - 1 / (current_year - 1992))
      // ...
      // Down to score * 1
      const eventYear = Number.parseInt(r.obj.key.slice(0, 4));
      const currentYear = Temporal.Now.plainDateISO().year;
      const yearDiff = currentYear - eventYear;
      const denominator = currentYear - 1992;

      return r.score * Math.max(1, 2 - yearDiff / denominator);
    },
  });

  return results.map((r) => ({ result: eventResult(r.obj), score: r.score }));
}

interface SearchDataFilterer {
  filter(data: SearchIndex, query: string): SearchResult[];
}

export default class FuzzysortFilterer implements SearchDataFilterer {
  filter(data: SearchIndex, query: string): SearchResult[] {
    const teamYear = findTeamYear(data.teams, query);
    if (teamYear) {
      return [teamYear];
    }

    return [
      ...searchTeams(data.teams, query),
      ...searchEvents(data.events, query),
    ]
      .sort((a, b) => b.score - a.score)
      .slice(0, RESULT_LIMIT)
      .map((r) => r.result);
  }
}
