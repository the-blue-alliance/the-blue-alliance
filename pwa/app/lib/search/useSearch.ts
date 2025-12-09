import { useEffect, useMemo, useState } from 'react';

import { SearchIndex } from '~/api/tba/read/types.gen';
import FuzzysortFilterer from '~/lib/search/fuzzysortFilterer';
import { ProdAPIProvider } from '~/lib/search/prodAPIProvider';

export const useSearch = () => {
  const [query, setQuery] = useState<string>('');
  const [searchIndex, setSearchIndex] = useState<SearchIndex | null>(null);
  const [searchResults, setSearchResults] = useState<SearchIndex | null>(null);
  const provider = useMemo(() => new ProdAPIProvider(), []);
  const filterer = useMemo(() => new FuzzysortFilterer(), []);

  useEffect(() => {
    provider
      .provide()
      .then((data) => setSearchIndex(data))
      .catch(() => {
        // TODO: Log in sentry
      });
  }, [provider]);

  useEffect(() => {
    if (searchIndex === null) {
      return;
    }

    const searchResults = filterer.filter(searchIndex, query);
    setSearchResults(searchResults);
  }, [query, searchIndex, filterer]);

  return {
    query,
    setQuery,
    searchResults,
    isSearchLoading: searchIndex === null,
  };
};
