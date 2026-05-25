import fuzzysort from 'fuzzysort';
import { Temporal } from 'temporal-polyfill';

import { SearchIndex } from '~/api/tba/read';

type SearchableTeam = SearchIndex['teams'][number];
type SearchableEvent = SearchIndex['events'][number];

export interface FilteredSearchIndex {
  teams: SearchableTeam[];
  events: SearchableEvent[];
  teamsFirst: boolean;
}

function searchTeams(
  teams: SearchableTeam[],
  query: string,
  limit: number,
): { results: SearchableTeam[]; topScore: number } {
  const results = fuzzysort.go(
    query,
    teams.map((t) => ({ ...t, team_number: Number(t.key.substring(3)) })),
    {
      limit,
      keys: ['key', 'nickname', 'team_number'],
      threshold: 0.5,
    },
  );

  return {
    results: results.map((result) => result.obj),
    topScore: results[0]?.score ?? -Infinity,
  };
}

function searchEvents(
  events: SearchableEvent[],
  query: string,
  limit: number,
): { results: SearchableEvent[]; topScore: number } {
  const results = fuzzysort.go(query, events, {
    limit,
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

  return {
    results: results.map((result) => result.obj),
    topScore: results[0]?.score ?? -Infinity,
  };
}

interface SearchDataFilterer {
  filter(data: SearchIndex, query: string): FilteredSearchIndex;
}

export default class FuzzysortFilterer implements SearchDataFilterer {
  filter(data: SearchIndex, query: string): FilteredSearchIndex {
    const teams = searchTeams(data.teams, query, 5);
    const events = searchEvents(data.events, query, 5);

    return {
      teams: teams.results,
      events: events.results,
      teamsFirst: teams.topScore >= events.topScore,
    };
  }
}
