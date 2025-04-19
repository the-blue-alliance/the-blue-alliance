import fuzzysort from 'fuzzysort';

import { SearchIndex } from '~/api/tba';
import { SearchDataFilterer } from '~/lib/search/api';

type SearchableTeam = SearchIndex['teams'][number];
type SearchableEvent = SearchIndex['events'][number];

function searchTeams(
  teams: SearchableTeam[],
  query: string,
  limit: number,
): SearchableTeam[] {
  const results = fuzzysort.go(query, teams, {
    limit,
    keys: ['key', 'nickname'],
    threshold: 0.5,
  });

  return results.map((result) => result.obj);
}

function searchEvents(
  events: SearchableEvent[],
  query: string,
  limit: number,
): SearchableEvent[] {
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
      const currentYear = new Date().getFullYear();
      const yearDiff = currentYear - eventYear;
      const denominator = currentYear - 1992;

      return r.score * Math.max(1, 2 - yearDiff / denominator);
    },
  });

  return results.map((result) => result.obj);
}

export default class FuzzysortFilterer implements SearchDataFilterer {
  filter(data: SearchIndex, query: string): SearchIndex {
    return {
      teams: searchTeams(data.teams, query, 5),
      events: searchEvents(data.events, query, 10),
    };
  }
}
