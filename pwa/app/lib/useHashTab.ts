import { useNavigate } from '@tanstack/react-router';
import { useCallback, useSyncExternalStore } from 'react';

function subscribeToHashChange(onChange: () => void): () => void {
  window.addEventListener('hashchange', onChange);
  return () => window.removeEventListener('hashchange', onChange);
}

function readRawHash(): string {
  return decodeURIComponent(window.location.hash.slice(1));
}

// The server has no hash; hydrating on the default tab avoids a mismatch
function serverHash(): undefined {
  return undefined;
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
 * `values` may change between renders (data-driven tabs): the hash is
 * matched against the current list on every render, so a hash naming a tab
 * that appears once its data loads takes effect at that point.
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
  // The store holds only the raw hash; which tab it names is decided during
  // render against the current `values`, so data-driven tab lists work too
  const rawHash = useSyncExternalStore(
    subscribeToHashChange,
    readRawHash,
    serverHash,
  );
  const candidate =
    rawHash === undefined ? undefined : (legacyHashes[rawHash] ?? rawHash);
  const hashTab =
    candidate !== undefined && (values as readonly string[]).includes(candidate)
      ? (candidate as T)
      : undefined;
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
