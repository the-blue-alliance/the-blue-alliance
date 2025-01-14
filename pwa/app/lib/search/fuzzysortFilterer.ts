import fuzzysort from 'fuzzysort';

import { SearchIndex } from '~/api/v3';
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
