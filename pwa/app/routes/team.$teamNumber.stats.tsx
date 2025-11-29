import { uniq } from 'lodash-es';
import { useMemo, useState } from 'react';
import { useLoaderData } from 'react-router';

import {
  getTeam,
  getTeamAwards,
  getTeamEvents,
  getTeamMatchesByYear,
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

import { Route } from '.react-router/types/app/routes/+types/team.$teamNumber.stats';

async function loadData(params: Route.LoaderArgs['params']) {
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
    throw new Response(null, { status: 404 });
  }

  const allMatchesByYear = await Promise.all(
    uniq(events.data.map((e) => e.year)).map((year) =>
      getTeamMatchesByYear({
        path: { team_key: `frc${params.teamNumber}`, year },
      }),
    ),
  );

  if (allMatchesByYear.some((resp) => resp.data === undefined)) {
    throw new Response(null, { status: 500 });
  }

  return {
    team: team.data,
    allMatchesByYear: allMatchesByYear.map((resp) => resp.data ?? []),
    allAwards: awards.data,
    allEvents: events.data,
    socials: socials.data,
    media: media.data,
  };
}

export async function loader({ params }: Route.LoaderArgs) {
  return await loadData(params);
}

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return await loadData(params);
}

export function meta({ data }: Route.MetaArgs) {
  if (!data) {
    return [
      {
        title: `Team Stats - The Blue Alliance`,
      },
    ];
  }

  return [
    {
      title: `${data.team.nickname} - Team ${data.team.team_number} (Stats) - The Blue Alliance`,
    },
  ];
}

export default function TeamStatsPage() {
  const { team, allMatchesByYear, allEvents, allAwards, socials, media } =
    useLoaderData<typeof loader>();

  const [includeOffseasons, setIncludeOffseasons] = useState(false);
  const [minYear, setMinYear] = useState(allEvents[0].year);
  const [maxYear, setMaxYear] = useState(allEvents[allEvents.length - 1].year);

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
      <TeamMatchStats
        teamKey={team.key}
        matches={usedMatches}
        events={usedEvents}
      />
    </div>
  );
}
