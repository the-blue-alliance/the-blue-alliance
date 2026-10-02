import { useNavigate } from '@tanstack/react-router';
import { useCallback, useState, useSyncExternalStore } from 'react';

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
 * The tabs are controlled by the returned `value`, so switching tabs only
 * re-renders; nothing remounts. The server never sees the hash, so the page
 * renders and hydrates on `defaultValue`; React then re-renders with the
 * client's hash. Clicks set the selection directly, and any later change to
 * the hash itself (back/forward, editing the address bar) is adopted too.
 *
 * `values` may change between renders (data-driven tabs): the selection is
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
  value: T;
  onValueChange: (value: string) => void;
} {
  const navigate = useNavigate();
  const rawHash = useSyncExternalStore(
    subscribeToHashChange,
    readRawHash,
    serverHash,
  );
  // Clicks select immediately; a hash we haven't seen yet (hydration,
  // back/forward) replaces the selection
  const [selection, setSelection] = useState({
    selected: rawHash,
    seenHash: rawHash,
  });
  let { selected } = selection;
  if (rawHash !== selection.seenHash) {
    selected = rawHash;
    setSelection({ selected: rawHash, seenHash: rawHash });
  }
  const candidate =
    selected === undefined ? undefined : (legacyHashes[selected] ?? selected);
  const value =
    candidate !== undefined && (values as readonly string[]).includes(candidate)
      ? (candidate as T)
      : defaultValue;
  const onValueChange = useCallback(
    (next: string) => {
      setSelection((prev) => ({ ...prev, selected: next }));
      void navigate({
        to: '.',
        hash: next,
        replace: true,
        resetScroll: false,
        hashScrollIntoView: false,
      });
    },
    [navigate],
  );
  return { value, onValueChange };
}
