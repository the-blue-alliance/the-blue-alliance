import { createFileRoute } from '@tanstack/react-router';
import { z } from 'zod';

import { GamedayFrame } from '~/components/tba/gameday/GamedayFrame';
import { GamedayProvider } from '~/lib/gameday/context';
import { publicCacheControlHeaders } from '~/lib/utils';

// Search params schema for gameday URL state
const gamedaySearchSchema = z.object({
  layout: z.coerce.number().int().optional(),
  view_0: z.string().optional(),
  view_1: z.string().optional(),
  view_2: z.string().optional(),
  view_3: z.string().optional(),
  view_4: z.string().optional(),
  view_5: z.string().optional(),
  view_6: z.string().optional(),
  view_7: z.string().optional(),
  view_8: z.string().optional(),
  chat: z.string().optional(),
});

export type GamedaySearchParams = z.infer<typeof gamedaySearchSchema>;

export const Route = createFileRoute('/gameday')({
  validateSearch: gamedaySearchSchema,
  headers: publicCacheControlHeaders(),
  head: () => ({
    meta: [
      { title: 'GameDay - The Blue Alliance' },
      {
        name: 'description',
        content:
          'Watch multiple live FRC event webcasts at once with GameDay by The Blue Alliance',
      },
    ],
  }),
  component: GamedayRoute,
});

function GamedayRoute() {
  return (
    <GamedayProvider>
      <GamedayFrame />
    </GamedayProvider>
  );
}
