import { QueryClient } from '@tanstack/react-query';
import { Temporal } from 'temporal-polyfill';

import { ApiError } from '~/lib/apiError';

/**
 * `staleTime` tiers for TanStack Query.
 *
 * `DEFAULT` is anchored to the TBA API's own `cache-control: max-age=61` header —
 * telling Query what the API already tells every other cache in the chain. This
 * alone prevents the hydration refetch storm: without it, `staleTime` defaults to
 * `0`, so every `useSuspenseQuery` treats data the server just sent as instantly
 * stale and refetches it on mount.
 *
 * `HISTORICAL` is for data that cannot change: a past season's events, team-years,
 * districts, etc. are immutable, so they can hold far longer than the default.
 *
 * `STATUS` is for `/status`, specifically the `current_season` / `max_season` /
 * `max_team_page` fields the PWA reads from it to pick default years and page bounds.
 * Those flip only a handful of times a year, so `/status` is fetched once (see the
 * root route's `beforeLoad`) and held for hours rather than re-awaited by every
 * route. `is_datafeed_down` / `down_events` are not consumed by these call sites, so
 * a long `staleTime` here doesn't risk showing stale outage banners.
 *
 * `SEARCH_INDEX` is for `/search_index`, the large all-teams + all-events blob used
 * by navbar search and team tooltips. It changes rarely (new teams/events), so it
 * is held for a full day to avoid refetching the heavy payload on navigations.
 *
 * Live data (in-progress matches, rankings) should NOT use any of the above — it
 * should keep a low `staleTime` (or the `DEFAULT`) alongside an explicit
 * `refetchInterval`, which fires independent of `staleTime`.
 */
export const STALE_TIME = {
  /** ~60s, matching the API's `max-age=61`. */
  DEFAULT: 60_000,
  /** 1h — for data that is known to be immutable (past seasons). */
  HISTORICAL: 60 * 60 * 1000,
  /** 6h — for `/status`, which changes at most a few times a year. */
  STATUS: 6 * 60 * 60 * 1000,
  /** 1d — for `/search_index`, which changes rarely. */
  SEARCH_INDEX: 24 * 60 * 60 * 1000,
} as const;

/**
 * Returns the appropriate `staleTime` for data scoped to a given (calendar) year.
 *
 * Past calendar years are immutable regardless of the current FRC season, so this
 * is a pure calendar comparison — deliberately independent of the `/status` API's
 * `current_season` (resolved once in the root route's `beforeLoad`, see
 * `app/routes/__root.tsx`). Reusing the same `Temporal.Now.plainDateISO().year`
 * pattern already used elsewhere in the app as the current-year fallback.
 */
export function staleTimeForYear(year: number): number {
  return year < Temporal.Now.plainDateISO().year
    ? STALE_TIME.HISTORICAL
    : STALE_TIME.DEFAULT;
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: STALE_TIME.DEFAULT,
        // Don't retry 4xx responses — they indicate a client or data error (e.g. 404
        // "not found") that won't resolve on retry. Retrying them causes unnecessary
        // background re-renders for the full exponential-backoff window (~10s).
        retry: (failureCount, error) => {
          if (
            error instanceof ApiError &&
            error.status >= 400 &&
            error.status < 500
          ) {
            return false;
          }
          return failureCount < 3;
        },
      },
    },
  });
}
