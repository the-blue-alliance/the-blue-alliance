import { SearchIndex } from '~/api/v3';

export interface SearchDataProvider {
  provide(): Promise<SearchIndex>;
}

export interface SearchDataFilterer {
  filter(data: SearchIndex, query: string): SearchIndex;
}
