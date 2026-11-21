import { SearchIndex } from '~/api/tba/read';
import { siteSearch } from '~/lib/search/siteSearch';

export interface SearchRedirectResult {
  type: 'team' | 'event' | 'no-results';
  path?: string;
  query: string;
}

export function getSearchRedirect(
  searchIndex: SearchIndex,
  query: string,
  currentSeason: number,
): SearchRedirectResult {
  const top = siteSearch(searchIndex, query, currentSeason).at(0);
  return top
    ? { type: top.type, path: top.path, query }
    : { type: 'no-results', query };
}
