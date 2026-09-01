import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { type InsightV2GameStats } from '~/api/tba/read';
import { getInsightsV2YearCategoryOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import { SuccessRateTable } from '~/components/tba/successRateInsight';
import { Tabs, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { staleTimeForYear } from '~/lib/queryClient';
import { type MatchLevel, otherMatchLevel } from '~/lib/successRateUtils';

/**
 * Success rates for a single event, read out of that season's `game_stats`
 * insight. There is no per-event endpoint for v2 insights - the year payload
 * carries one scope per event, so we fetch it and pick this event's scope out.
 */
export function EventSuccessRateTable({
  eventKey,
  year,
}: {
  eventKey: string;
  year: number;
}) {
  const [matchLevel, setMatchLevel] = useState<MatchLevel>('qual');

  const insightsQuery = useQuery({
    ...getInsightsV2YearCategoryOptions({
      path: { year, category: 'game_stats' },
    }),
    staleTime: staleTimeForYear(year),
  });

  // The route is category-filtered, but the response type is the full
  // discriminated union, so narrow before reaching into `data`.
  const insight = insightsQuery.data?.find(
    (i): i is InsightV2GameStats => i.category === 'game_stats',
  );
  const scope = insight?.data.scopes.find(
    (s) => s.scope_type === 'event' && s.key === eventKey,
  );

  // Seasons without bonus ranking points produce no insight at all, and an
  // event with no played matches gets no scope.
  if (scope === undefined) {
    return null;
  }

  const rates = scope[matchLevel];
  const fallbackLevel = otherMatchLevel(matchLevel);

  return (
    <div className="mt-6">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-semibold">Success Rates</h3>
        <Tabs
          value={matchLevel}
          onValueChange={(value) => {
            setMatchLevel(value as MatchLevel);
          }}
        >
          <TabsList>
            <TabsTrigger value="qual">Quals</TabsTrigger>
            <TabsTrigger value="playoff">Playoffs</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {rates.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No {matchLevel === 'qual' ? 'qualification' : 'playoff'} match data
          for this event.
          {scope[fallbackLevel].length > 0 &&
            ` Try the ${fallbackLevel === 'qual' ? 'Quals' : 'Playoffs'} tab.`}
        </p>
      ) : (
        <SuccessRateTable rates={rates} />
      )}
    </div>
  );
}
