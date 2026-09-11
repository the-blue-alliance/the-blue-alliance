import { useNavigate } from '@tanstack/react-router';
import { useCallback, useSyncExternalStore } from 'react';

function subscribeToHashChange(onChange: () => void): () => void {
  window.addEventListener('hashchange', onChange);
  return () => window.removeEventListener('hashchange', onChange);
}

/**
 * Keeps a tab bar in sync with the URL hash: `/event/2024mil#rankings` opens
 * the Rankings tab, and picking a tab rewrites the hash (replace, not push, so
 * the back button still leaves the page).
 *
 * The tabs stay uncontrolled. The server never sees the hash, so the page
 * renders and hydrates on `defaultValue`; once the client reads the hash the
 * returned `key` changes and the tab bar remounts on the hashed tab. Our own
 * tab clicks use history.replaceState, which fires no `hashchange`, so they
 * never remount; only external changes (initial load, back/forward) do.
 *
 * `legacyHashes` maps hash names the Jinja site used to today's tab values so
 * old links keep landing on the right tab.
 */
export function useHashTab<T extends string>({
  values,
  defaultValue,
  legacyHashes = {},
}: {
  values: readonly T[];
  defaultValue: T;
  legacyHashes?: Record<string, T>;
}): {
  key: string;
  defaultValue: T;
  onValueChange: (value: string) => void;
} {
  const navigate = useNavigate();
  const readHash = useCallback((): T | undefined => {
    const hash = window.location.hash.slice(1);
    const value = legacyHashes[hash] ?? hash;
    return (values as readonly string[]).includes(value)
      ? (value as T)
      : undefined;
    // values/legacyHashes are static per call site
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const hashTab = useSyncExternalStore(
    subscribeToHashChange,
    readHash,
    () => undefined,
  );
  const onValueChange = useCallback(
    (value: string) => {
      void navigate({
        to: '.',
        hash: value,
        replace: true,
        resetScroll: false,
        hashScrollIntoView: false,
      });
    },
    [navigate],
  );
  return {
    key: hashTab ?? '',
    defaultValue: hashTab ?? defaultValue,
    onValueChange,
  };
}
