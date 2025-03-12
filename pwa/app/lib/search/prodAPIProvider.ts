import { SearchIndex, getSearchIndex } from '~/api/v3';
import { SearchDataProvider } from '~/lib/search/api';

export class ProdAPIProvider implements SearchDataProvider {
  async provide(): Promise<SearchIndex> {
    const searchIndex = await getSearchIndex({});

    if (searchIndex.status !== 200) {
      return Promise.reject(new Error('Failed to fetch search index'));
    }

    return searchIndex.data;
  }
}
