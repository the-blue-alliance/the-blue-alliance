import { SearchIndex } from '~/api/tba/read';
import FuzzysortFilterer from '~/lib/search/fuzzysortFilterer';

export interface SearchRedirectResult {
  type: 'team' | 'event' | 'no-results';
  path?: string;
  query: string;
}

/**
 * Determines the best redirect target for a search query.
 * Uses fuzzy search to find the top team and event matches,
 * then redirects to whichever has the higher score.
 * Teams win ties (common case: numeric searches match team numbers).
 *
 * @param searchIndex - The search index containing teams and events
 * @param query - The search query string
 * @returns A SearchRedirectResult indicating where to redirect (or no-results)
 */
export function getSearchRedirect(
  searchIndex: SearchIndex,
  query: string,
): SearchRedirectResult {
  // Normalize query
  const normalizedQuery = query.trim();

  // Return no-results if empty
  if (!normalizedQuery) {
    return { type: 'no-results', query };
  }

  // Use FuzzysortFilterer to search both teams and events
  const filterer = new FuzzysortFilterer();
  const results = filterer.filter(searchIndex, normalizedQuery);

  const topTeam = results.teams[0];
  const topEvent = results.events[0];

  // If we have no matches, return no-results
  if (!topTeam && !topEvent) {
    return { type: 'no-results', query };
  }

  // If we only have a team match, redirect to it
  if (topTeam && !topEvent) {
    // Strip "frc" prefix from team key (e.g., "frc254" -> "254")
    const teamNumber = topTeam.key.substring(3);
    return {
      type: 'team',
      path: `/team/${teamNumber}`,
      query,
    };
  }

  // If we only have an event match, redirect to it
  if (topEvent && !topTeam) {
    return {
      type: 'event',
      path: `/event/${topEvent.key}`,
      query,
    };
  }

  // if we have both (we shouldn't), just redirect to the team
  const teamNumber = topTeam.key.substring(3);
  return {
    type: 'team',
    path: `/team/${teamNumber}`,
    query,
  };
}
