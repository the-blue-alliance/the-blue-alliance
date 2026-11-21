import { useEffect, useState } from 'react';

export function useIsHydrated() {
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => {
    // eslint-disable-next-line react/set-state-in-effect -- deferred by design so markup matches during hydration
    setHydrated(true);
  }, []);
  return hydrated;
}

/**
 * From https://github.com/redpangilinan/credenza
 *
 * Returns false during SSR and the first client render, then the real match, so
 * hydration-sensitive consumers such as Credenza stay deterministic.
 */
export function useMediaQuery(query: string) {
  const [value, setValue] = useState(false);

  useEffect(() => {
    function onChange(event: MediaQueryListEvent) {
      setValue(event.matches);
    }

    const result = matchMedia(query);
    result.addEventListener('change', onChange);
    // eslint-disable-next-line react/set-state-in-effect -- deferred by design, see doc comment
    setValue(result.matches);

    return () => {
      result.removeEventListener('change', onChange);
    };
  }, [query]);

  return value;
}
