import { SearchIndex } from '~/api/tba/read';

export interface SearchDataProvider {
  provide(): Promise<SearchIndex>;
}

export interface SearchDataFilterer {
  filter(data: SearchIndex, query: string): SearchIndex;
}
