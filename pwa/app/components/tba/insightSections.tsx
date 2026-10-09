import { type Event } from '~/api/tba/read';
import { Leaderboard } from '~/components/tba/leaderboard';
import { StreakInsight } from '~/components/tba/streakInsight';
import { SuccessRateInsight } from '~/components/tba/successRateInsight';
import { TimeseriesInsight } from '~/components/tba/timeseriesInsight';
import { type GroupedInsights } from '~/lib/insightUtils';

interface InsightSectionsProps extends GroupedInsights {
  year: number;
  eventsByKey: ReadonlyMap<string, Event>;
}

function SectionHeading({ children }: { children: string }) {
  return (
    <h2 className="mb-4 flex items-center gap-2 text-2xl font-semibold">
      <span
        className="inline-block h-1 w-8 rounded-full bg-linear-to-r from-primary
          to-primary/50"
      />
      {children}
    </h2>
  );
}

export function InsightSections({
  year,
  eventsByKey,
  leaderboards,
  streaks,
  timeseries,
  successRates,
}: InsightSectionsProps) {
  return (
    <>
      {successRates.length > 0 && (
        <div className="mb-8">
          <SectionHeading>Success Rates</SectionHeading>
          <div className="grid gap-6">
            {successRates.map((sr) => (
              <SuccessRateInsight
                subtitle={sr.year > 0 ? `${sr.year} Season` : 'Overall'}
                insight={sr}
                key={sr.name}
              />
            ))}
          </div>
        </div>
      )}

      {leaderboards.length > 0 && (
        <div className="mb-8">
          <SectionHeading>Leaderboards</SectionHeading>
          <div
            className="grid
              grid-cols-[repeat(auto-fill,minmax(min(100%,25rem),1fr))] gap-6"
          >
            {leaderboards.map((l) => (
              <Leaderboard
                subtitle={l.year > 0 ? `${l.year}` : 'Overall'}
                leaderboard={l}
                displayName={l.display_name}
                key={l.name}
                year={year}
                eventsByKey={eventsByKey}
              />
            ))}
          </div>
        </div>
      )}

      {streaks.length > 0 && (
        <div className="mb-8">
          <SectionHeading>Streaks</SectionHeading>
          <div
            className="grid
              grid-cols-[repeat(auto-fill,minmax(min(100%,25rem),1fr))] gap-6"
          >
            {streaks.map((s) => (
              <StreakInsight
                subtitle={s.year > 0 ? `${s.year}` : 'Overall'}
                streak={s}
                key={s.name}
              />
            ))}
          </div>
        </div>
      )}

      {timeseries.length > 0 && (
        <div>
          <SectionHeading>Timeseries</SectionHeading>
          <div
            className="grid
              grid-cols-[repeat(auto-fill,minmax(min(100%,25rem),1fr))] gap-6"
          >
            {timeseries.map((t) => (
              <TimeseriesInsight
                subtitle={t.year > 0 ? `${t.year}` : 'Overall'}
                timeseries={t}
                key={t.name}
              />
            ))}
          </div>
        </div>
      )}
    </>
  );
}
