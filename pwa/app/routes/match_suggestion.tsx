import * as ProgressPrimitive from '@radix-ui/react-progress';
import { useQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';
import {
  type ComponentPropsWithoutRef,
  type ElementRef,
  type JSX,
  forwardRef,
  useState,
} from 'react';
import { Temporal } from 'temporal-polyfill';

import MedalIcon from '~icons/lucide/medal';
import TrophyIcon from '~icons/lucide/trophy';

import {
  AwardType,
  CompLevel,
  Event,
  EventRanking,
  Match,
  MediaAvatar,
  PlayoffType,
  getEventMatches,
  getEventOprs,
  getEventPredictions,
  getEventRankings,
  getEventsByYear,
  getInsightsNotablesYear,
  getStatus,
  getTeamEventsStatusesByYear,
} from '~/api/tba/read';
import {
  getDistrictRankingsOptions,
  getEventOptions,
  getTeamAwardsByYearOptions,
  getTeamDistrictsOptions,
  getTeamEventsByYearOptions,
  getTeamMediaByYearOptions,
  getTeamOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { EventLink, TeamLink } from '~/components/tba/links';
import SimpleMatchRowsWithBreaks from '~/components/tba/match/matchRows';
import TeamAvatar from '~/components/tba/teamAvatar';
import { Badge } from '~/components/ui/badge';
import {
  EVENT_FALLBACK_TIMEZONE,
  getCurrentWeekEvents,
} from '~/lib/eventUtils';
import { matchTitleShort, sortMatchComparator } from '~/lib/matchUtils';
import { cn, publicCacheControlHeaders, queryFromAPI } from '~/lib/utils';

export const Route = createFileRoute('/match_suggestion')({
  loader: async () => {
    const status = await getStatus();

    if (status.data === undefined) {
      throw new Error('Failed to load status');
    }

    const year = status.data.current_season;
    const events = await getEventsByYear({ path: { year } });

    if (events.data === undefined) {
      throw new Error('Failed to load events');
    }

    const filteredEvents = getCurrentWeekEvents(events.data);

    return {
      events: filteredEvents,
    };
  },
  headers: publicCacheControlHeaders(),
  component: MatchSuggestion,
});

// TODO: Fix this typing
interface EventPredictions {
  match_predictions?: {
    qual: Record<
      string,
      {
        red: {
          score: number;
          endGameTowerPoints: number;
        };
        blue: {
          score: number;
          endGameTowerPoints: number;
        };
      }
    >;
    playoff: Record<
      string,
      {
        red: { score: number; endGameTowerPoints: number };
        blue: { score: number; endGameTowerPoints: number };
      }
    >;
  };
}

interface MatchInfo {
  match: Match;
  event: Event;
  eventRankings?: EventRanking | null;
  eventPredictions?: EventPredictions | null;
  epaPercentileMap?: Map<string, number> | null;
}

function epaStars(percentile: number | undefined): string {
  if (percentile == null) return '';
  if (percentile >= 0.9975) return '⭐⭐⭐⭐⭐';
  if (percentile >= 0.995) return '⭐⭐⭐⭐';
  if (percentile >= 0.99) return '⭐⭐⭐';
  if (percentile >= 0.98) return '⭐⭐';
  if (percentile >= 0.975) return '⭐';
  return '';
}

const Progress = forwardRef<
  ElementRef<typeof ProgressPrimitive.Root>,
  ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>
>(({ className, value, ...props }, ref) => (
  <ProgressPrimitive.Root
    ref={ref}
    className={cn(
      'relative h-4 w-full overflow-hidden rounded-full bg-secondary',
      className,
    )}
    {...props}
  >
    <ProgressPrimitive.Indicator
      className="size-full flex-1 bg-primary transition-all"
      style={{ transform: `translateX(-${100 - (value ?? 0)}%)` }}
    />
  </ProgressPrimitive.Root>
));
Progress.displayName = ProgressPrimitive.Root.displayName;

function EventName({ eventKey }: { eventKey: string }) {
  const eventQuery = useQuery(
    getEventOptions({ path: { event_key: eventKey } }),
  );
  if (!eventQuery.data) {
    return eventKey;
  }
  return <>{eventQuery.data.name}</>;
}

function TeamDetails({
  teamKey,
  className,
  defaultRed = false,
}: {
  teamKey: string;
  className: string;
  defaultRed?: boolean;
}) {
  const teamQuery = useQuery(getTeamOptions({ path: { team_key: teamKey } }));
  const teamMediaQuery = useQuery({
    ...getTeamMediaByYearOptions({ path: { team_key: teamKey, year: 2026 } }),
    select: (media) => media.find((m): m is MediaAvatar => m.type === 'avatar'),
  });
  const eventStatusesQuery = useQuery({
    queryKey: ['teamEventStatusByYear', teamKey, 2026],
    queryFn: () =>
      queryFromAPI(
        getTeamEventsStatusesByYear({
          path: { team_key: teamKey, year: 2026 },
        }),
      ),
  });
  const teamEventsByYearQuery = useQuery(
    getTeamEventsByYearOptions({ path: { team_key: teamKey, year: 2026 } }),
  );
  const eventOprsQuery = useQuery({
    queryKey: ['eventOprs', teamKey, 2026],
    enabled: !!teamEventsByYearQuery.data,
    queryFn: async () => {
      const results = await Promise.all(
        (teamEventsByYearQuery.data ?? []).map((e) =>
          getEventOprs({ path: { event_key: e.key } }),
        ),
      );
      const map = new Map<string, number>();
      (teamEventsByYearQuery.data ?? []).forEach((e, i) => {
        const opr = results[i].data?.oprs?.[teamKey];
        if (opr != null) map.set(e.key, opr);
      });
      return map;
    },
  });
  const teamAwardsByYearQuery = useQuery(
    getTeamAwardsByYearOptions({ path: { team_key: teamKey, year: 2026 } }),
  );
  const teamDistrictsQuery = useQuery(
    getTeamDistrictsOptions({ path: { team_key: teamKey } }),
  );
  const district2026 = teamDistrictsQuery.data?.find((d) => d.year === 2026);
  const district2026Key = district2026?.key;
  const district2026Abbrev = district2026?.abbreviation.toUpperCase();
  const districtRankingsQuery = useQuery({
    ...getDistrictRankingsOptions({
      path: { district_key: district2026Key ?? '' },
    }),
    enabled: !!district2026Key,
    select: (rankings) => ({
      entry: (rankings ?? []).find((r) => r.team_key === teamKey),
      total: (rankings ?? []).length,
    }),
  });

  const insightNotablesYearQuery = useQuery({
    queryKey: ['insightNotablesYear', 0],
    queryFn: () => queryFromAPI(getInsightsNotablesYear({ path: { year: 0 } })),
  });
  const divisionWinnersNotable = insightNotablesYearQuery.data
    ?.find((insight) => insight.name == 'notables_division_winners')
    ?.data.entries.find((notable) => notable.team_key == teamKey);

  const epaQuery = useQuery({
    queryKey: ['epaQuery', teamKey],
    queryFn: async () => {
      const response = await fetch(
        `https://api.statbotics.io/v3/team_year/${teamKey.substring(3)}/2026`,
      );
      // eslint-disable-next-line
      return response.json();
    },
  });

  // eslint-disable-next-line
  const epaBreakdown: {
    total_points: number;
    auto_fuel: number;
    teleop_fuel: number;
    total_tower: number;
  } | null = // eslint-disable-next-line
    epaQuery.data ? epaQuery.data.epa.breakdown : null;

  if (
    !teamQuery.data ||
    !eventStatusesQuery.data ||
    !insightNotablesYearQuery.data
  ) {
    return (
      <td className={cn('text-left', className)} colSpan={2}>
        Loading...
      </td>
    );
  }

  const divisionWins = divisionWinnersNotable
    ? divisionWinnersNotable.context.map((eventKey) => eventKey.substring(0, 4))
    : [];

  const eventInfoMap = new Map(
    (teamEventsByYearQuery.data ?? []).map((e) => [
      e.key,
      { startDate: e.start_date, week: e.week },
    ]),
  );

  const statuses = [];
  for (const [key, value] of Object.entries(eventStatusesQuery.data)) {
    const info = eventInfoMap.get(key);
    statuses.push({
      event: key,
      rank: value?.qual?.ranking?.rank,
      alliance: value?.alliance
        ? `A${value.alliance.number}${value.alliance.pick == 0 ? 'C' : `P${value.alliance.pick}`}`
        : 'DNP',
      finish:
        value?.playoff?.status == 'won'
          ? 'Winner'
          : value?.playoff?.level == CompLevel.F
            ? 'Finalist'
            : '?',
      week: info?.week ?? null,
      startDate: info?.startDate ?? key,
    });
  }
  statuses.sort((a, b) =>
    a.startDate < b.startDate ? 1 : a.startDate > b.startDate ? -1 : 0,
  );

  const awardsByEvent = new Map<string, { name: string; type: AwardType }[]>();
  for (const award of teamAwardsByYearQuery.data ?? []) {
    // Skip Winner/Finalist — already shown via the finish field
    if (
      award.award_type === AwardType.WINNER ||
      award.award_type === AwardType.FINALIST
    ) {
      continue;
    }
    const list = awardsByEvent.get(award.event_key) ?? [];
    list.push({ name: award.name, type: award.award_type });
    awardsByEvent.set(award.event_key, list);
  }

  return (
    <div className={cn('rounded-lg p-3 text-left', className)}>
      {/* Header */}
      <div className="mb-2">
        <div className="flex items-center gap-2">
          {teamMediaQuery.data && (
            <TeamAvatar
              media={teamMediaQuery.data}
              className="shrink-0"
              defaultRed={defaultRed}
            />
          )}
          <div>
            <div className="text-base leading-tight font-bold">
              <TeamLink teamOrKey={teamQuery.data} year={2026} target="_blank">
                #{teamQuery.data.team_number}
              </TeamLink>{' '}
              &mdash; {teamQuery.data.nickname}
            </div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              {teamQuery.data.city}, {teamQuery.data.state_prov},{' '}
              {teamQuery.data.country}
            </div>
            {districtRankingsQuery.data?.entry && (
              <div className="mt-0.5 text-xs text-muted-foreground">
                {district2026Abbrev} Rank:{' '}
                <span className="font-semibold text-foreground">
                  #{districtRankingsQuery.data.entry.rank}
                </span>
                {' / '}
                {districtRankingsQuery.data.total}
                {' · '}
                <span className="font-semibold text-foreground">
                  {districtRankingsQuery.data.entry.point_total}
                </span>{' '}
                pts
              </div>
            )}
          </div>
        </div>
      </div>

      <hr className="mb-2" />

      {/* EPA Stats */}
      <div className="mb-2">
        <div
          className="mb-1 text-xs font-semibold tracking-wide
            text-muted-foreground uppercase"
        >
          EPA (Statbotics)
        </div>
        <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-sm">
          <div>
            <span className="font-medium">Total</span>{' '}
            <span className="float-right font-mono">
              {epaBreakdown ? epaBreakdown.total_points.toFixed(1) : '—'}
            </span>
          </div>
          <div>
            <span className="font-medium">Tower</span>{' '}
            <span className="float-right font-mono">
              {epaBreakdown ? epaBreakdown.total_tower.toFixed(1) : '—'}
            </span>
          </div>
          <div>
            <span className="font-medium">Auto Fuel</span>{' '}
            <span className="float-right font-mono">
              {epaBreakdown ? epaBreakdown.auto_fuel.toFixed(1) : '—'}
            </span>
          </div>
          <div>
            <span className="font-medium">Tele Fuel</span>{' '}
            <span className="float-right font-mono">
              {epaBreakdown ? epaBreakdown.teleop_fuel.toFixed(1) : '—'}
            </span>
          </div>
        </div>
      </div>

      {/* Past Einstein */}
      {divisionWins.length > 0 && (
        <>
          <hr className="mb-2" />
          <div className="mb-2 flex flex-wrap gap-1">
            <span
              className="text-xs font-semibold tracking-wide
                text-muted-foreground uppercase"
            >
              Einstein:
            </span>
            {divisionWins.map((year) => (
              <Badge key={year} className="text-xs">
                {year}
              </Badge>
            ))}
          </div>
        </>
      )}

      {/* Per-event statuses */}
      {statuses.length > 0 && (
        <>
          <hr className="mb-2" />
          <div className="space-y-1.5">
            {statuses.map((status) => (
              <div
                key={status.event}
                className="rounded border border-border bg-background/50 px-2
                  py-1.5 text-sm"
              >
                <div
                  className="flex items-baseline gap-1.5 truncate font-medium"
                >
                  {status.week != null && (
                    <span
                      className="shrink-0 rounded bg-muted px-1 py-0.5
                        text-[10px] font-semibold text-muted-foreground"
                    >
                      {status.week === 0 ? 'Pre' : `Wk ${status.week}`}
                    </span>
                  )}
                  <span className="truncate">
                    <EventLink eventOrKey={status.event} target="_blank">
                      <EventName eventKey={status.event} />
                    </EventLink>
                  </span>
                </div>
                <div className="space-y-0.5 text-xs text-muted-foreground">
                  <div className="grid grid-cols-2 gap-x-2">
                    <span>
                      Rank:{' '}
                      <span className="font-semibold text-foreground">
                        {status.rank ?? '—'}
                      </span>
                    </span>
                    <span>
                      Alliance:{' '}
                      <span className="font-semibold text-foreground">
                        {status.alliance}
                      </span>
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-x-2">
                    <span>
                      Finish:{' '}
                      <span
                        className="inline-flex items-center gap-0.5
                          font-semibold text-foreground"
                      >
                        {status.finish === 'Winner' && (
                          <TrophyIcon className="size-3 text-yellow-500" />
                        )}
                        {status.finish === 'Finalist' && (
                          <MedalIcon className="size-3 text-slate-400" />
                        )}
                        {status.finish}
                      </span>
                    </span>
                    <span>
                      OPR:{' '}
                      <span className="font-semibold text-foreground">
                        {eventOprsQuery.data?.has(status.event)
                          ? (
                              eventOprsQuery.data.get(status.event) ?? 0
                            ).toFixed(1)
                          : '—'}
                      </span>
                    </span>
                  </div>
                </div>
                {(awardsByEvent.get(status.event) ?? []).length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {(awardsByEvent.get(status.event) ?? []).map((award, i) => {
                      const isImpact = award.type === AwardType.CHAIRMANS;
                      const isEI =
                        award.type === AwardType.ENGINEERING_INSPIRATION;
                      return (
                        <span
                          key={i}
                          className={cn(
                            'rounded px-1 py-0.5 text-[10px] font-semibold',
                            isImpact &&
                              `bg-yellow-100 text-yellow-800 dark:bg-yellow-900
                              dark:text-yellow-200`,
                            isEI &&
                              `bg-blue-100 text-blue-800 dark:bg-blue-900
                              dark:text-blue-200`,
                            !isImpact &&
                              !isEI &&
                              'bg-muted text-muted-foreground',
                          )}
                        >
                          {award.name}
                        </span>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function MatchSuggestionRow({
  match,
  event,
  eventRankings,
  eventPredictions,
  epaPercentileMap,
}: MatchInfo) {
  const [showDetails, setShowDetails] = useState(false);

  const prediction =
    eventPredictions?.match_predictions?.qual[match.key] ??
    eventPredictions?.match_predictions?.playoff[match.key];

  const predictedRedScore = prediction ? prediction.red.score : 0.0;
  const predictedBlueScore = prediction ? prediction.blue.score : 0.0;

  const redEndGamePoints = prediction ? prediction.red.endGameTowerPoints : 0.0;
  const blueEndGamePoints = prediction
    ? prediction.blue.endGameTowerPoints
    : 0.0;

  const blueZoneScore =
    100 *
    Math.min(
      1.0,
      (Math.max(predictedRedScore, predictedBlueScore) +
        2.0 * Math.min(predictedRedScore, predictedBlueScore)) /
        3000.0,
    );

  return (
    <>
      <tr key={match.key} className="text-center">
        <td className="border">{event.key.substring(4).toUpperCase()}</td>
        <td className="border">
          {matchTitleShort(match, event.playoff_type ?? PlayoffType.CUSTOM)}
        </td>
        <td className="border">
          {match.predicted_time && (
            <span>
              {Temporal.Instant.fromEpochMilliseconds(
                match.predicted_time * 1000,
              )
                .toZonedDateTimeISO(event.timezone ?? EVENT_FALLBACK_TIMEZONE)
                .toLocaleString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit',
                  weekday: 'short',
                  hour12: true,
                })}
            </span>
          )}
        </td>
        {match.alliances.red.team_keys.map((k) => (
          <td className="border bg-alliance-red-loser" key={k}>
            <TeamLink teamOrKey={k} year={event.year}>
              {k.substring(3)}
            </TeamLink>
            <br />(
            {eventRankings?.rankings.find((r) => r.team_key == k)?.rank ?? '?'})
            {epaStars(epaPercentileMap?.get(k)) && (
              <>
                <br />
                <span className="text-xs">
                  {epaStars(epaPercentileMap?.get(k))}
                </span>
              </>
            )}
          </td>
        ))}
        {match.alliances.blue.team_keys.map((k) => (
          <td className="border bg-alliance-blue-loser" key={k}>
            <TeamLink teamOrKey={k} year={event.year}>
              {k.substring(3)}
            </TeamLink>
            <br />(
            {eventRankings?.rankings.find((r) => r.team_key == k)?.rank ?? '?'})
            {epaStars(epaPercentileMap?.get(k)) && (
              <>
                <br />
                <span className="text-xs">
                  {epaStars(epaPercentileMap?.get(k))}
                </span>
              </>
            )}
          </td>
        ))}
        <td className="border bg-alliance-red-winner">
          {predictedRedScore.toFixed(0)}
        </td>
        <td className="border bg-alliance-blue-winner">
          {predictedBlueScore.toFixed(0)}
        </td>
        <td className="border bg-alliance-red-loser">
          {redEndGamePoints.toFixed(0)}
          <Progress value={(redEndGamePoints / 36.0) * 100.0} />
        </td>
        <td className="border bg-alliance-blue-loser">
          {blueEndGamePoints.toFixed(0)}
          <Progress value={(blueEndGamePoints / 36.0) * 100.0} />
        </td>
        <td className="border">
          {blueZoneScore.toFixed(0)}
          <Progress value={blueZoneScore} />
        </td>
        <td className="border">
          <Badge
            className="ml-2 cursor-pointer"
            onClick={() => {
              setShowDetails((prev) => !prev);
            }}
          >
            {showDetails ? 'Hide' : 'Show'}
          </Badge>
        </td>
      </tr>
      {showDetails && (
        <tr>
          <td colSpan={17}>
            <div className="grid grid-cols-6 gap-4 py-4">
              {match.alliances.red.team_keys.map((k) => (
                <TeamDetails
                  key={k}
                  teamKey={k}
                  className="bg-alliance-red-loser"
                  defaultRed
                />
              ))}
              {match.alliances.blue.team_keys.map((k) => (
                <TeamDetails
                  key={k}
                  teamKey={k}
                  className="bg-alliance-blue-loser"
                />
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function MatchSuggestion(): JSX.Element {
  const { events } = Route.useLoaderData();

  const eventMatchesQuery = useQuery({
    queryKey: ['eventMatches', events],
    queryFn: () =>
      Promise.all(
        events.map(async (event) =>
          (
            await queryFromAPI(
              getEventMatches({ path: { event_key: event.key } }),
            )
          ).sort(sortMatchComparator),
        ),
      ),
  });

  const eventRankingsQuery = useQuery({
    queryKey: ['eventRankings', events],
    queryFn: () =>
      Promise.all(
        events.map(async (event) => {
          const x = await getEventRankings({ path: { event_key: event.key } });
          if (x.data === undefined) {
            return null;
          }

          return x.data;
        }),
      ),
  });

  const eventPredictionsQuery = useQuery({
    queryKey: ['eventPredictions', events],
    queryFn: () =>
      Promise.all(
        events.map(
          async (event) =>
            await queryFromAPI(
              getEventPredictions({ path: { event_key: event.key } }),
            ),
        ),
      ),
  });
  const epaPercentilesQuery = useQuery({
    queryKey: ['epaPercentiles', 2026],
    queryFn: async () => {
      const response = await fetch(
        'https://api.statbotics.io/v3/team_years?year=2026',
      );
      // eslint-disable-next-line
      const allTeams: {
        team: number;
        epa: { ranks: { total: { percentile: number } } };
      }[] = await response.json();
      const map = new Map<string, number>();
      for (const entry of allTeams) {
        map.set(`frc${entry.team}`, entry.epa.ranks.total.percentile);
      }
      return map;
    },
    staleTime: 10 * 60 * 1000,
  });

  if (!eventMatchesQuery.data) {
    return <div>No matches!</div>;
  }

  const finishedMatches: Match[] = [];
  const currentMatches: MatchInfo[] = [];
  const upcomingMatches: MatchInfo[] = [];

  eventMatchesQuery.data.forEach((eventMatches, eventIdx) => {
    const lastMatch = eventMatches.findLast(
      (match) =>
        match.alliances.red.score !== -1 && match.alliances.blue.score !== -1,
    );
    if (lastMatch) {
      finishedMatches.push(lastMatch);
    }

    const unplayedMatches = eventMatches.filter(
      (match) =>
        match.alliances.red.score === -1 || match.alliances.blue.score === -1,
    );
    unplayedMatches.forEach((match, i) => {
      if (i > 2) {
        return;
      }
      if (i == 0) {
        currentMatches.push({
          match,
          event: events[eventIdx],
          eventRankings: eventRankingsQuery.data?.[eventIdx],
          eventPredictions: eventPredictionsQuery.data?.[eventIdx] ?? null,
          epaPercentileMap: epaPercentilesQuery.data ?? null,
        });
      } else {
        upcomingMatches.push({
          match,
          event: events[eventIdx],
          eventRankings: eventRankingsQuery.data?.[eventIdx],
          eventPredictions: eventPredictionsQuery.data?.[eventIdx],
          epaPercentileMap: epaPercentilesQuery.data ?? null,
        });
      }
    });
  });

  finishedMatches.sort(
    (a, b) => (a.actual_time ?? a.time ?? 0) - (b.actual_time ?? b.time ?? 0),
  );
  currentMatches.sort(
    (a, b) =>
      (a.match.predicted_time ?? a.match.time ?? 0) -
      (b.match.predicted_time ?? b.match.time ?? 0),
  );
  upcomingMatches.sort(
    (a, b) =>
      (a.match.predicted_time ?? a.match.time ?? 0) -
      (b.match.predicted_time ?? b.match.time ?? 0),
  );

  return (
    <div className="w-full px-4 py-8">
      <h1 className="text-3xl font-medium">Match Suggestions</h1>
      <Badge
        className="ml-2 cursor-pointer"
        onClick={() => {
          void (async () => {
            await Promise.all([
              eventMatchesQuery.refetch(),
              eventRankingsQuery.refetch(),
              eventPredictionsQuery.refetch(),
              epaPercentilesQuery.refetch(),
            ]);
          })();
        }}
      >
        Refresh
      </Badge>
      <h2 className="text-2xl font-medium">Finished Matches</h2>
      {/* This is a hack for now. */}
      <SimpleMatchRowsWithBreaks
        matches={finishedMatches}
        event={events[0]}
        breakers={[]}
      />
      <div className="my-4 text-sm text-muted-foreground">
        <span className="font-semibold text-foreground">Key:</span> ⭐⭐⭐⭐⭐
        Top 0.25% · ⭐⭐⭐⭐ Top 0.5% · ⭐⭐⭐ Top 1% · ⭐⭐ Top 2% · ⭐ Top
        2.5%
      </div>
      <h2 className="text-2xl font-medium">Current Matches</h2>
      <table className="w-[100%]">
        <thead>
          <tr>
            <th className="border">Event</th>
            <th className="border">Match</th>
            <th className="border">Time</th>
            <th className="border">R1 (Rank)</th>
            <th className="border">R2 (Rank)</th>
            <th className="border">R3 (Rank)</th>
            <th className="border">B1 (Rank)</th>
            <th className="border">B2 (Rank)</th>
            <th className="border">B3 (Rank)</th>
            <th className="border">Red Predicted Score</th>
            <th className="border">Blue Predicted Score</th>
            <th className="border">Red Tower Points</th>
            <th className="border">Blue Tower Points</th>
            <th className="border">BlueZone Score</th>
            <th className="border">Details</th>
          </tr>
        </thead>
        <tbody>
          {currentMatches.map((matchInfo) => (
            <MatchSuggestionRow key={matchInfo.match.key} {...matchInfo} />
          ))}
        </tbody>
      </table>
      <h2 className="text-2xl font-medium">Upcoming Matches</h2>
      <table className="w-[100%]">
        <thead>
          <tr>
            <th className="border">Event</th>
            <th className="border">Match</th>
            <th className="border">Time</th>
            <th className="border">R1 (Rank)</th>
            <th className="border">R2 (Rank)</th>
            <th className="border">R3 (Rank)</th>
            <th className="border">B1 (Rank)</th>
            <th className="border">B2 (Rank)</th>
            <th className="border">B3 (Rank)</th>
            <th className="border">Red Predicted Score</th>
            <th className="border">Blue Predicted Score</th>
            <th className="border">Red Tower Points</th>
            <th className="border">Blue Tower Points</th>
            <th className="border">BlueZone Score</th>
            <th className="border">Details</th>
          </tr>
        </thead>
        <tbody>
          {upcomingMatches.map((matchInfo) => (
            <MatchSuggestionRow key={matchInfo.match.key} {...matchInfo} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
