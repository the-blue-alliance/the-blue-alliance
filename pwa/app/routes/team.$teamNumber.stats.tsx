import { useQueries } from '@tanstack/react-query';
import { createFileRoute, notFound, useNavigate } from '@tanstack/react-router';
import { uniq } from 'lodash-es';
import { useMemo, useState } from 'react';

import MdiCog from '~icons/mdi/cog';
import MdiRobotExcited from '~icons/mdi/robot-excited';

import { getTeamMatchesByYearOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import {
  getTeam,
  getTeamAwards,
  getTeamEvents,
  getTeamMediaByYear,
  getTeamSocialMedia,
} from '~/api/tba/read/sdk.gen';
import { DoubleSlider } from '~/components/tba/doubleSlider';
import TeamAwardsSummary from '~/components/tba/teamAwardsSummary';
import TeamMatchStats from '~/components/tba/teamMatchStats';
import TeamPageTeamInfo from '~/components/tba/teamPageTeamInfo';
import { Checkbox } from '~/components/ui/checkbox';
import { Divider } from '~/components/ui/divider';
import { SEASON_EVENT_TYPES } from '~/lib/api/EventType';
import { sortAwardsByEventDate } from '~/lib/awardUtils';
import { sortEventsComparator } from '~/lib/eventUtils';
import { sortMultipleEventsMatches } from '~/lib/matchUtils';
import { publicCacheControlHeaders } from '~/lib/utils';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '~/components/ui/select';

export const Route = createFileRoute('/team/$teamNumber/stats')({
  loader: async ({ params }) => {
    const [team, events, awards, socials, media] = await Promise.all([
      getTeam({ path: { team_key: `frc${params.teamNumber}` } }),
      getTeamEvents({ path: { team_key: `frc${params.teamNumber}` } }),
      getTeamAwards({ path: { team_key: `frc${params.teamNumber}` } }),
      getTeamSocialMedia({ path: { team_key: `frc${params.teamNumber}` } }),
      getTeamMediaByYear({
        path: {
          team_key: `frc${params.teamNumber}`,
          year: new Date().getFullYear(),
        },
      }),
    ]);
    if (
      team.data === undefined ||
      events.data === undefined ||
      awards.data === undefined ||
      socials.data === undefined ||
      media.data === undefined
    ) {
      throw notFound();
    }

    return {
      team: team.data,
      allAwards: awards.data,
      allEvents: events.data,
      socials: socials.data,
      media: media.data,
    };
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
            text-blue-300 direction-[reverse]"
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
  const { team, allEvents, allAwards, socials, media } = Route.useLoaderData();

  const navigate = useNavigate();

  const [includeOffseasons, setIncludeOffseasons] = useState(false);
  const [minYear, setMinYear] = useState(allEvents[0].year);
  const [maxYear, setMaxYear] = useState(allEvents[allEvents.length - 1].year);

  const [yearsParticipated, setYearsParticipated] = useState([...new Set(allEvents.map((event, i) => event.year))].sort((a, b) => b - a));

  const maybeAvatar = useMemo(() => {
    return media.find((m) => m.type === 'avatar');
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

  const matchQueriesNumLoaded = useMemo(() => {
    return matchQueries.filter((q) => q.isSuccess).length;
  }, [matchQueries]);

  const allMatchesByYear = useMemo(
    () => matchQueries.map((q) => q.data ?? []),
    [matchQueries],
  );

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
    <div>
      <div className=" flex w-full flex-row justify-between gap-[5px]">
        <div className="top-0 pt-5 sm:sticky">
          <Select
            onValueChange={(value) => {
              void navigate({
                to: '/team/$teamNumber/{-$year}',
                params: { teamNumber: String(team.team_number), year: value },
              });
            }}
            value='stats'
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder={'Stats'} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="history">History</SelectItem>
              <SelectItem value="stats">Stats</SelectItem>
              {yearsParticipated.map((y) => (
                <SelectItem key={y} value={`${y}`}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="mt-8">
          <TeamPageTeamInfo
            team={team}
            maybeAvatar={maybeAvatar}
            socials={socials}
          />
        </div>
        <div className="flex flex-col gap-2 mt-8">
          <div className="flex flex-row items-center gap-2">
            <Checkbox
              checked={includeOffseasons}
              onCheckedChange={(checked) =>
                setIncludeOffseasons(
                  checked === 'indeterminate' ? false : checked,
                )
              }
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
  );
}
