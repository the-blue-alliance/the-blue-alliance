import { SearchIndex } from '~/api/tba/read';
import FuzzysortFilterer from '~/lib/search/fuzzysortFilterer';

export interface SearchRedirectResult {
  type: 'team' | 'event' | 'no-results';
  path?: string;
  query: string;
}

export function getSearchRedirect(
  searchIndex: SearchIndex,
  query: string,
): SearchRedirectResult {
  const normalizedQuery = query.trim();
  if (!normalizedQuery) {
    return { type: 'no-results', query };
  }

  const top = new FuzzysortFilterer()
    .filter(searchIndex, normalizedQuery)
    .at(0);
  return top
    ? { type: top.type, path: top.path, query }
    : { type: 'no-results', query };
}
