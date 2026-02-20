import { createFileRoute, redirect } from '@tanstack/react-router';
import { z } from 'zod';

import { getSearchIndexOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import { getSearchRedirect } from '~/lib/search/searchRedirect';
import { publicCacheControlHeaders } from '~/lib/utils';

const searchSchema = z.object({
  q: z.string().optional().default(''),
});

export const Route = createFileRoute('/search')({
  validateSearch: searchSchema,
  beforeLoad: async ({ context: { queryClient }, search }) => {
    const searchIndex = await queryClient.ensureQueryData(
      getSearchIndexOptions({}),
    );
    // Tanstack may auto-parse '604' to a number, so just stringify it just in case
    const result = getSearchRedirect(searchIndex, search.q.toString());

    // If we found a team or event, redirect to it
    if (result.type === 'team' || result.type === 'event') {
      throw redirect({ to: result.path });
    }

    // Otherwise, pass query to component
    return { query: search.q };
  },
  headers: publicCacheControlHeaders(),
  head: () => ({
    meta: [
      { title: 'Search - The Blue Alliance' },
      {
        name: 'description',
        content: 'Search for teams and events on The Blue Alliance',
      },
    ],
  }),
  component: SearchRoute,
});

function SearchRoute() {
  const { query } = Route.useRouteContext();

  return (
    <div className="container max-w-2xl py-8">
      <h1 className="mb-4 text-3xl font-medium">No Results Found</h1>
      {query && (
        <p className="mb-4 text-muted-foreground">
          No results found for &quot;{query}&quot;
        </p>
      )}
      <div className="rounded-lg border bg-muted/50 p-6">
        <h2 className="mb-3 text-xl font-medium">Search Tips</h2>
        <p className="mb-3">Try searching for:</p>
        <ul className="list-inside list-disc space-y-1 text-muted-foreground">
          <li>Team numbers (e.g., &quot;254&quot;, &quot;604&quot;)</li>
          <li>
            Team nicknames (e.g., &quot;Cheesy Poofs&quot;,
            &quot;Quixilver&quot;)
          </li>
          <li>Event keys (e.g., &quot;2024casj&quot;, &quot;2024mil&quot;)</li>
          <li>Event names (e.g., &quot;Silicon Valley Regional&quot;)</li>
        </ul>
      </div>
    </div>
  );
}
