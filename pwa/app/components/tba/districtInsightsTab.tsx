import { useQuery } from '@tanstack/react-query';

import { type Event } from '~/api/tba/read';
import {
  getEventsByYearOptions,
  getInsightsV2YearDistrictOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { InsightSections } from '~/components/tba/insightSections';
import { Spinner } from '~/components/ui/spinner';
import { groupInsightsByCategory } from '~/lib/insightUtils';
import { staleTimeForYear } from '~/lib/queryClient';

interface DistrictInsightsTabProps {
  abbreviation: string;
  year: number;
}

export function DistrictInsightsTab({
  abbreviation,
  year,
}: DistrictInsightsTabProps) {
  const staleTime = staleTimeForYear(year);
  const insightsQuery = useQuery({
    ...getInsightsV2YearDistrictOptions({
      path: { year, district_abbreviation: abbreviation },
    }),
    staleTime,
  });
  const eventsQuery = useQuery({
    ...getEventsByYearOptions({ path: { year } }),
    staleTime,
  });

  if (insightsQuery.isPending || eventsQuery.isPending) {
    return <Spinner className="mx-auto mt-16 size-8" />;
  }

  const insights = insightsQuery.data ?? [];
  if (insights.length === 0) {
    return (
      <p className="mt-8 text-center text-muted-foreground">
        No insights for this district in {year}.
      </p>
    );
  }

  const eventsByKey = new Map<string, Event>(
    (eventsQuery.data ?? []).map((event) => [event.key, event]),
  );

  return (
    <div className="pt-4">
      <InsightSections
        year={year}
        eventsByKey={eventsByKey}
        {...groupInsightsByCategory(insights)}
      />
    </div>
  );
}
