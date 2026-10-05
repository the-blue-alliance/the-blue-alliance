import { useLocation, useNavigate } from '@tanstack/react-router';
import { useCallback, useState } from 'react';

import { useIsHydrated } from '~/lib/hooks';

/**
 * Keeps a tab bar in sync with the URL hash: `/event/2024mil#rankings` opens
 * the Rankings tab, and picking a tab rewrites the hash (replace, not push, so
 * the back button still leaves the page).
 *
 * The tabs are controlled by the returned `value`, so switching tabs only
 * re-renders; nothing remounts. The router's location is the single source of
 * truth for the hash, so back/forward and address-bar edits are picked up
 * too. A click shows its tab immediately while the router's navigation
 * finishes. The server never sees the hash, so the page renders and hydrates
 * on `defaultValue` and switches to the hash's tab once hydrated.
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
  const isHydrated = useIsHydrated();
  const routerHash = useLocation({ select: (location) => location.hash });
  // The tab just clicked, shown until the router's location catches up
  const [pending, setPending] = useState<string>();
  const hash = decodeURIComponent(routerHash);
  if (pending !== undefined && pending === hash) {
    setPending(undefined);
  }
  // The server has no hash, so render and hydrate on the default tab
  const selected = isHydrated ? (pending ?? hash) : undefined;
  const candidate =
    selected === undefined ? undefined : (legacyHashes[selected] ?? selected);
  const value =
    candidate !== undefined && (values as readonly string[]).includes(candidate)
      ? (candidate as T)
      : defaultValue;
  const onValueChange = useCallback(
    (next: string) => {
      setPending(next);
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
