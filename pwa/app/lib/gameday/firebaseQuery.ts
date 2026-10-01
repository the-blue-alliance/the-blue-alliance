/**
 * Placeholder `queryFn` for TanStack queries whose data is written exclusively
 * via `setQueryData` from a Firebase subscription. TanStack Query v5 requires a
 * `queryFn` even with `enabled: false`; these queries are never fetched, so
 * this only runs if something explicitly refetches them, and then it resolves
 * to "no data" rather than throwing.
 */
export function firebaseOnlyQueryFn(): null {
  return null;
}
