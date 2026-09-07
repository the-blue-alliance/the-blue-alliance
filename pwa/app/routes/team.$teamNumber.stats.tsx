import { useQueries, useQuery, useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';
import { uniq } from 'lodash-es';
import { useMemo, useState } from 'react';
import { Temporal } from 'temporal-polyfill';

import MdiCog from '~icons/mdi/cog';
import MdiRobotExcited from '~icons/mdi/robot-excited';

import { MediaAvatar } from '~/api/tba/read';
import {
  getTeamAwardsOptions,
  getTeamEventsOptions,
  getTeamMatchesByYearOptions,
  getTeamMediaByYearOptions,
  getTeamOptions,
  getTeamSocialMediaOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { DoubleSlider } from '~/components/tba/doubleSlider';
import TeamAwardsSummary from '~/components/tba/teamAwardsSummary';
import TeamMatchStats from '~/components/tba/teamMatchStats';
import TeamPageTeamInfo from '~/components/tba/teamPageTeamInfo';
import { YearSelector } from '~/components/tba/yearSelector';
import { Checkbox } from '~/components/ui/checkbox';
import { Divider } from '~/components/ui/divider';
import { SEASON_EVENT_TYPES } from '~/lib/api/EventType';
import { sortAwardsByEventDate } from '~/lib/awardUtils';
import { sortEventsComparator } from '~/lib/eventUtils';
import { sortMultipleEventsMatches } from '~/lib/matchUtils';
import { doThrowNotFound, publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/team/$teamNumber/stats')({
  loader: async ({ params, context: { queryClient } }) => {
    const teamKey = `frc${params.teamNumber}`;
    // Resolved once here so the loader and the component build the same query
    // key, rather than each reading the clock independently.
    const mediaYear = Temporal.Now.plainDateISO().year;

    // spawn these now, we don't need to await them yet though
    const awardsQuery = queryClient
      .ensureQueryData(getTeamAwardsOptions({ path: { team_key: teamKey } }))
      .catch(() => []);
    const socialsQuery = queryClient
      .ensureQueryData(
        getTeamSocialMediaOptions({ path: { team_key: teamKey } }),
      )
      .catch(() => []);
    const mediaQuery = queryClient
      .ensureQueryData(
        getTeamMediaByYearOptions({
          path: { team_key: teamKey, year: mediaYear },
        }),
      )
      .catch(() => []);

    const [team] = await Promise.all([
      queryClient
        .ensureQueryData(getTeamOptions({ path: { team_key: teamKey } }))
        .catch(doThrowNotFound),
      queryClient
        .ensureQueryData(getTeamEventsOptions({ path: { team_key: teamKey } }))
        .catch(doThrowNotFound),
      awardsQuery,
      socialsQuery,
      mediaQuery,
    ]);

    // team needs to be returned so we can access it in meta
    return { teamKey, mediaYear, team };
  },
  headers: publicCacheControlHeaders(),
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [{ title: 'Team Stats - The Blue Alliance' }],
      };
    }

    return {
      meta: [
        {
          title: `${loaderData.team.nickname} - Team ${loaderData.team.team_number} (Stats) - The Blue Alliance`,
        },
      ],
    };
  },
  component: TeamStatsPage,
});

function MatchStatsLoadingState({
  numLoaded,
  total,
}: {
  numLoaded: number;
  total: number;
}) {
  const progress = total > 0 ? (numLoaded / total) * 100 : 0;

  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="relative mb-6">
        <MdiRobotExcited className="size-16 animate-bounce text-blue-500" />
        <MdiCog
          className="absolute -top-2 -right-4 size-8 animate-spin text-blue-400"
        />
        <MdiCog
          className="absolute -bottom-1 -left-3 size-6 animate-spin
            text-blue-300 direction-reverse"
        />
      </div>
      <div className="mb-3 text-lg font-medium text-foreground">
        Compiling match data...
      </div>
      <div className="mb-2 text-sm text-muted-foreground">
        {numLoaded} / {total} years loaded
      </div>
      <div className="h-2 w-64 overflow-hidden rounded-full bg-neutral-200">
        <div
          className="h-full bg-blue-500 transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

function TeamStatsPage() {
  const { teamKey, mediaYear } = Route.useLoaderData();

  const { data: team } = useSuspenseQuery(
    getTeamOptions({ path: { team_key: teamKey } }),
  );
  const { data: allEvents } = useSuspenseQuery(
    getTeamEventsOptions({ path: { team_key: teamKey } }),
  );
  const awardsQuery = useQuery(
    getTeamAwardsOptions({ path: { team_key: teamKey } }),
  );
  const allAwards = useMemo(() => awardsQuery.data ?? [], [awardsQuery.data]);
  const socialsQuery = useQuery(
    getTeamSocialMediaOptions({ path: { team_key: teamKey } }),
  );
  const socials = socialsQuery.data ?? [];
  const mediaQuery = useQuery(
    getTeamMediaByYearOptions({
      path: { team_key: teamKey, year: mediaYear },
    }),
  );
  const media = useMemo(() => mediaQuery.data ?? [], [mediaQuery.data]);

  const [includeOffseasons, setIncludeOffseasons] = useState(false);
  const [minYear, setMinYear] = useState(allEvents[0].year);
  const [maxYear, setMaxYear] = useState(allEvents[allEvents.length - 1].year);

  const yearsParticipated = useMemo(
    () => uniq(allEvents.map((e) => e.year)).sort((a, b) => b - a),
    [allEvents],
  );

  const maybeAvatar = useMemo(() => {
    return media.find((m): m is MediaAvatar => m.type === 'avatar');
  }, [media]);

  const usedEvents = useMemo(() => {
    return allEvents
      .filter(
        (event) =>
          event.year >= minYear &&
          event.year <= maxYear &&
          (includeOffseasons || SEASON_EVENT_TYPES.has(event.event_type)),
      )
      .sort(sortEventsComparator);
  }, [allEvents, minYear, maxYear, includeOffseasons]);

  const usedAwards = useMemo(() => {
    const eventKeys = new Set(usedEvents.map((event) => event.key));
    return sortAwardsByEventDate(
      allAwards.filter(
        (award) =>
          eventKeys.has(award.event_key) &&
          award.year >= minYear &&
          award.year <= maxYear,
      ),
      usedEvents,
    );
  }, [allAwards, usedEvents, minYear, maxYear]);

  const matchQueries = useQueries({
    queries: uniq(allEvents.map((e) => e.year)).map((year) =>
      getTeamMatchesByYearOptions({
        path: { team_key: team.key, year },
      }),
    ),
  });

  const matchQueriesNumLoaded = matchQueries.filter((q) => q.isSuccess).length;

  const allMatchesByYear = matchQueries.map((q) => q.data ?? []);

  const usedMatches = useMemo(() => {
    const eventKeys = new Set(usedEvents.map((event) => event.key));
    return sortMultipleEventsMatches(
      allMatchesByYear
        .flat()
        .filter(
          (match) =>
            eventKeys.has(match.event_key) &&
            Number(match.event_key.slice(0, 4)) >= minYear &&
            Number(match.event_key.slice(0, 4)) <= maxYear,
        ),
      usedEvents,
    );
  }, [allMatchesByYear, usedEvents, minYear, maxYear]);

  return (
    <div className="flex flex-wrap sm:flex-nowrap">
      <div className="top-0 mr-4 pt-5 sm:sticky">
        <YearSelector
          currentLabel="Stats"
          triggerClassName="w-[180px]"
          options={[
            {
              label: 'History',
              to: `/team/${team.team_number}/history`,
            },
            {
              label: 'Stats',
              to: `/team/${team.team_number}/stats`,
              isCurrent: true,
            },
            ...yearsParticipated.map((y) => ({
              label: String(y),
              to: `/team/${team.team_number}/${y}`,
            })),
          ]}
        />
      </div>
      <div className="w-full">
        <div className="mt-8 flex w-full flex-row justify-between">
          <div>
            <TeamPageTeamInfo
              team={team}
              maybeAvatar={maybeAvatar}
              socials={socials}
            />
          </div>
          <div className="flex flex-col gap-2">
            <div className="flex flex-row items-center gap-2">
              <Checkbox
                checked={includeOffseasons}
                onCheckedChange={setIncludeOffseasons}
              />
              <span className="text-sm text-muted-foreground">
                Include Offseasons
              </span>
            </div>
            <DoubleSlider
              min={allEvents[0].year}
              max={allEvents[allEvents.length - 1].year}
              value={[minYear, maxYear]}
              onValueChange={(value) => {
                setMinYear(value[0]);
                setMaxYear(value[1]);
              }}
              minStepsBetweenThumbs={0}
              step={1}
            />
          </div>
        </div>
        <Divider className="my-4" />
        <TeamAwardsSummary awards={usedAwards} events={usedEvents} />
        <Divider className="my-4" />
        {matchQueriesNumLoaded < matchQueries.length ? (
          <MatchStatsLoadingState
            numLoaded={matchQueriesNumLoaded}
            total={matchQueries.length}
          />
        ) : (
          <TeamMatchStats
            teamKey={team.key}
            matches={usedMatches}
            events={usedEvents}
          />
        )}
      </div>
    </div>
  );
}
