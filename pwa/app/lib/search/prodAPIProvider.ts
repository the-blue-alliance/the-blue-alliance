import { SearchIndex, getSearchIndex } from '~/api/tba';
import { SearchDataProvider } from '~/lib/search/api';

export class ProdAPIProvider implements SearchDataProvider {
  async provide(): Promise<SearchIndex> {
    const searchIndex = await getSearchIndex({});

    if (searchIndex.data === undefined) {
      return Promise.reject(new Error('Failed to fetch search index'));
    }

    return searchIndex.data;
  }
}
