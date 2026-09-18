import { useEffect, useMemo, useState } from 'react';
import { Temporal } from 'temporal-polyfill';

import AlertTriangleIcon from '~icons/lucide/triangle-alert';

import type { MatchSuggestion } from '~/api/firebase';
import { EventLink, MatchLink } from '~/components/tba/links';
import TeamListSubgrid from '~/components/tba/match/teamListSubgrid';
import { Spinner } from '~/components/ui/spinner';
import { useFirebaseMatchSuggestions } from '~/lib/gameday/useFirebaseMatchSuggestions';

const TIME_REFRESH_INTERVAL_MS = 30_000;

export function sortMatchSuggestions(
  suggestions: MatchSuggestion[],
): MatchSuggestion[] {
  return [...suggestions].sort(
    (a, b) => b.sc - a.sc || a.r - b.r || a.mk.localeCompare(b.mk),
  );
}

export function formatMatchTime(
  timestamp: number | null | undefined,
  now: Temporal.Instant,
  timeZone: string,
): string {
  if (timestamp == null) return 'Time unavailable';

  const target = Temporal.Instant.fromEpochMilliseconds(timestamp * 1000);
  const deltaSeconds = Math.round(
    (target.epochMilliseconds - now.epochMilliseconds) / 1000,
  );
  const absoluteSeconds = Math.abs(deltaSeconds);

  let relative: string;
  if (absoluteSeconds < 60) {
    relative = 'now';
  } else {
    const unit = absoluteSeconds < 60 * 60 ? 'min' : 'hr';
    const divisor = unit === 'min' ? 60 : 60 * 60;
    const amount = Math.max(1, Math.round(absoluteSeconds / divisor));
    relative =
      deltaSeconds > 0 ? `in ${amount} ${unit}` : `${amount} ${unit} ago`;
  }

  const localTime = target
    .toZonedDateTimeISO(timeZone)
    .toLocaleString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    });
  return `${relative} · ${localTime}`;
}

function AllianceTeams({
  alliance,
  teams,
  year,
}: {
  alliance: 'red' | 'blue';
  teams: number[];
  year: number;
}) {
  return (
    <TeamListSubgrid
      allianceColor={alliance}
      teamKeys={teams.map((team) => `frc${team}`)}
      dq={[]}
      surrogate={[]}
      year={year}
      className="col-span-3 rounded"
    />
  );
}

function Recommendation({
  suggestion,
  now,
  timeZone,
}: {
  suggestion: MatchSuggestion;
  now: Temporal.Instant;
  timeZone: string;
}) {
  const scores: [string, number][] = [
    ['Score', suggestion.sc],
    ['Favorites', suggestion.c.f],
    ['Significance', suggestion.c.sig],
    ['Time', suggestion.c.td],
    ['High Score', suggestion.c.hs],
    ['Close Score', suggestion.c.cs],
  ];

  return (
    <article className="space-y-2 border-b border-border p-3 last:border-b-0">
      <div className="flex items-start justify-between gap-3 text-sm">
        <div className="min-w-0">
          <EventLink
            eventOrKey={suggestion.ek}
            className="block truncate font-medium text-foreground
              hover:underline"
          >
            {suggestion.esn ?? suggestion.en}
          </EventLink>
          <MatchLink
            matchOrKey={suggestion.mk}
            noModal
            className="text-muted-foreground hover:underline"
          >
            {suggestion.dn}
          </MatchLink>
        </div>
        <span className="shrink-0 text-right text-xs text-muted-foreground">
          {formatMatchTime(suggestion.pt ?? suggestion.st, now, timeZone)}
        </span>
      </div>
      <div className="grid gap-1 sm:grid-cols-2">
        <AllianceTeams
          alliance="red"
          teams={suggestion.rt}
          year={Number(suggestion.ek.slice(0, 4))}
        />
        <AllianceTeams
          alliance="blue"
          teams={suggestion.bt}
          year={Number(suggestion.ek.slice(0, 4))}
        />
      </div>
      <dl
        aria-label="Recommendation scores"
        className="grid grid-cols-6 gap-1 text-center text-[10px]
          text-muted-foreground"
      >
        {scores.map(([label, score]) => (
          <div key={label} className="min-w-0">
            <dt className="truncate">{label}</dt>
            <dd className="font-mono text-foreground">{score.toFixed(2)}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}

export function MatchRecommendationsPanel() {
  const { data, error, isLoading } = useFirebaseMatchSuggestions();
  const [now, setNow] = useState(() => Temporal.Now.instant());
  const timeZone = Temporal.Now.timeZoneId();

  useEffect(() => {
    const interval = window.setInterval(
      () => setNow(Temporal.Now.instant()),
      TIME_REFRESH_INTERVAL_MS,
    );
    return () => window.clearInterval(interval);
  }, []);

  const suggestions = useMemo(
    () => sortMatchSuggestions(Object.values(data?.suggestions ?? {})),
    [data],
  );

  if (isLoading) {
    return (
      <div
        className="flex h-full items-center justify-center
          text-muted-foreground"
      >
        <Spinner className="mr-2" /> Loading recommendations…
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex h-full flex-col items-center justify-center px-6
          text-center text-muted-foreground"
      >
        <AlertTriangleIcon className="mb-2 size-7 text-amber-400" />
        <p>Unable to load match recommendations</p>
      </div>
    );
  }

  if (suggestions.length === 0) {
    return (
      <div
        className="flex h-full items-center justify-center px-6 text-center
          text-muted-foreground"
      >
        No upcoming match recommendations
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-background text-foreground">
      {suggestions.map((suggestion) => (
        <Recommendation
          key={suggestion.mk}
          suggestion={suggestion}
          now={now}
          timeZone={timeZone}
        />
      ))}
    </div>
  );
}
