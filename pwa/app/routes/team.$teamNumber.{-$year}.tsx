import { metrics } from '@sentry/tanstackstart-react';
import { useQueries, useQuery, useSuspenseQuery } from '@tanstack/react-query';
import {
  Link,
  createFileRoute,
  notFound,
  redirect,
} from '@tanstack/react-router';
import { useMemo, useState } from 'react';
import { Temporal } from 'temporal-polyfill';

import {
  Award,
  District,
  DistrictRanking,
  Event,
  EventType,
  Match,
  MediaAvatar,
  RegionalAdvancement,
  RegionalRanking,
  Team,
} from '~/api/tba/read';
import {
  getDistrictRankingsOptions,
  getEventAlliancesOptions,
  getEventAwardsOptions,
  getEventDistrictPointsOptions,
  getEventMatchesOptions,
  getRegionalAdvancementOptions,
  getRegionalChampsPoolPointsOptions,
  getRegionalRankingsOptions,
  getTeamAwardsByYearOptions,
  getTeamDistrictsOptions,
  getTeamEventStatusOptions,
  getTeamEventsByYearOptions,
  getTeamEventsStatusesByYearOptions,
  getTeamMatchesByYearOptions,
  getTeamMediaByYearOptions,
  getTeamOptions,
  getTeamSocialMediaOptions,
  getTeamYearsParticipatedOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { AwardBanner } from '~/components/tba/banner';
import FavoriteButton from '~/components/tba/favoriteButton';
import { DistrictLink } from '~/components/tba/links';
import {
  TableOfContents,
  TableOfContentsSection,
} from '~/components/tba/tableOfContents';
import TeamEventAppearance, {
  RobotAppearance,
} from '~/components/tba/teamEventAppearance';
import TeamMediaGallery from '~/components/tba/teamMediaGallery';
import TeamPageTeamInfo from '~/components/tba/teamPageTeamInfo';
import TeamRobotPicsCarousel from '~/components/tba/teamRobotPicsCarousel';
import { YearSelector } from '~/components/tba/yearSelector';
import { Separator } from '~/components/ui/separator';
import { BLUE_BANNER_AWARDS } from '~/lib/api/AwardType';
import { DISTRICT_EVENT_TYPES, SEASON_EVENT_TYPES } from '~/lib/api/EventType';
import { sortAwardsByEventDate } from '~/lib/awardUtils';
import { getRemappedRobots, sortEventsComparator } from '~/lib/eventUtils';
import {
  calculateRobotsRecord,
  calculateTeamRecordsFromMatches,
} from '~/lib/matchUtils';
import { getEmbedMedia, getImageMedia } from '~/lib/mediaUtils';
import { staleTimeForYear } from '~/lib/queryClient';
import { avatarYearForTeamPage } from '~/lib/teamUtils';
import {
  MODEL_TYPE,
  addRecords,
  doThrowNotFound,
  hasAnyMatches,
  parseParamsForYearElseDefault,
  publicCacheControlHeaders,
} from '~/lib/utils';

export const Route = createFileRoute('/team/$teamNumber/{-$year}')({
  loader: async ({ params, context: { queryClient, currentSeason } }) => {
    const startTime = Temporal.Now.instant().epochMilliseconds;
    const teamKey = `frc${params.teamNumber}`;
    const year = parseParamsForYearElseDefault(currentSeason, params);

    metrics.count('team.page.view', 1, {
      attributes: { team_number: params.teamNumber, year },
    });

    if (year === undefined) {
      throw notFound();
    }

    const yearStaleTime = staleTimeForYear(year);

    // spawn these now, we don't need to await them yet though
    const teamMediaQuery = queryClient
      .ensureQueryData({
        ...getTeamMediaByYearOptions({ path: { team_key: teamKey, year } }),
        staleTime: yearStaleTime,
      })
      .catch(() => []);
    const teamSocialsQuery = queryClient
      .ensureQueryData(
        getTeamSocialMediaOptions({ path: { team_key: teamKey } }),
      )
      .catch(() => ({}));
    const teamMatchesQuery = queryClient
      .ensureQueryData({
        ...getTeamMatchesByYearOptions({ path: { team_key: teamKey, year } }),
        staleTime: yearStaleTime,
      })
      .catch(() => []);
    const teamStatusesQuery = queryClient
      .ensureQueryData({
        ...getTeamEventsStatusesByYearOptions({
          path: { team_key: teamKey, year },
        }),
        staleTime: yearStaleTime,
      })
      .catch(() => ({}));
    const teamAwardsQuery = queryClient
      .ensureQueryData({
        ...getTeamAwardsByYearOptions({ path: { team_key: teamKey, year } }),
        staleTime: yearStaleTime,
      })
      .catch(() => []);
    const teamEventsQuery = queryClient
      .ensureQueryData({
        ...getTeamEventsByYearOptions({ path: { team_key: teamKey, year } }),
        staleTime: yearStaleTime,
      })
      .catch(() => []);
    const teamDistrictsQuery = queryClient
      .ensureQueryData(getTeamDistrictsOptions({ path: { team_key: teamKey } }))
      .catch(() => []);
    const remappedRobotsQuery = teamEventsQuery.then((events) =>
      Promise.all(
        events.flatMap((e) => {
          const robots = getRemappedRobots(e, teamKey);
          if (robots.length === 0) {
            return [];
          }
          return [
            queryClient
              .ensureQueryData({
                ...getEventMatchesOptions({ path: { event_key: e.key } }),
                staleTime: yearStaleTime,
              })
              .catch(() => []),
            queryClient
              .ensureQueryData({
                ...getEventAwardsOptions({ path: { event_key: e.key } }),
                staleTime: yearStaleTime,
              })
              .catch(() => []),
            ...robots.map((r) =>
              queryClient
                .ensureQueryData({
                  ...getTeamEventStatusOptions({
                    path: { team_key: r.sourceTeamKey, event_key: e.key },
                  }),
                  staleTime: yearStaleTime,
                })
                .catch(() => null),
            ),
          ];
        }),
      ),
    );

    // these need to be awaited so we can validate the year
    const [team, yearsParticipated] = await Promise.all([
      queryClient
        .ensureQueryData(getTeamOptions({ path: { team_key: teamKey } }))
        .catch(doThrowNotFound),
      queryClient
        .ensureQueryData(
          getTeamYearsParticipatedOptions({ path: { team_key: teamKey } }),
        )
        // Distinguish "fetch failed" from "team genuinely has no years" —
        // coercing a failure to [] would make the check below always redirect
        // or 404, even though the failure was already reported (see
        // ~/lib/queryClient.ts's onError) and has nothing to do with the year.
        .catch((): number[] | null => null),
    ]);

    if (yearsParticipated !== null && !yearsParticipated.includes(year)) {
      if (params.year === undefined) {
        throw redirect({
          to: '/team/$teamNumber/history',
          params: { teamNumber: params.teamNumber },
        });
      }
      throw notFound();
    }

    const avatarYear = avatarYearForTeamPage(
      year,
      yearsParticipated,
      currentSeason,
    );
    const avatarMediaQuery = queryClient
      .ensureQueryData({
        ...getTeamMediaByYearOptions({
          path: { team_key: teamKey, year: avatarYear },
        }),
        staleTime: staleTimeForYear(avatarYear),
      })
      .catch(() => []);

    await Promise.all([
      // await the earlier queries
      teamMediaQuery,
      avatarMediaQuery,
      teamSocialsQuery,
      teamMatchesQuery,
      teamStatusesQuery,
      teamAwardsQuery,
      teamEventsQuery,
      teamDistrictsQuery,
      remappedRobotsQuery,
    ]);

    const endTime = Temporal.Now.instant().epochMilliseconds;
    const duration = endTime - startTime;
    metrics.distribution('team.page.loader.duration', duration, {
      attributes: { team_number: params.teamNumber, year },
    });

    // team needs to be returned so we can access it in meta
    return {
      teamKey,
      year,
      avatarYear,
      team,
    };
  },
  headers: publicCacheControlHeaders(),
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [
          { title: 'Team Information - The Blue Alliance' },
          {
            name: 'description',
            content: 'Team information for the FIRST Robotics Competition.',
          },
        ],
      };
    }

    const { team } = loaderData;
    const location = [
      team.city,
      [team.state_prov, team.postal_code].filter(Boolean).join(' '),
      team.country,
    ]
      .filter(Boolean)
      .join(', ');
    const jsonLd = {
      '@context': 'https://schema.org',
      '@type': 'SportsTeam',
      name: `Team ${team.team_number} - ${team.nickname}`,
      url: `https://www.thebluealliance.com/team/${team.team_number}`,
      location: {
        '@type': 'Place',
        address: {
          '@type': 'PostalAddress',
          addressLocality: team.city,
          addressRegion: team.state_prov,
          postalCode: team.postal_code,
          addressCountry: team.country,
        },
      },
      memberOf: {
        '@type': 'SportsOrganization',
        name: 'FIRST Robotics Competition',
        url: 'https://www.firstinspires.org',
      },
    };

    return {
      meta: [
        {
          title: `${team.nickname} - Team ${team.team_number} - The Blue Alliance`,
        },
        {
          name: 'description',
          content: `${location ? `From ${location}. ` : ''}Team information, match results, and match videos from the FIRST Robotics Competition.`,
        },
      ],
      scripts: [
        {
          type: 'application/ld+json',
          children: JSON.stringify(jsonLd),
        },
      ],
    };
  },
  component: TeamPage,
}); // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop

function TeamPage(): React.JSX.Element {
  const { teamKey, year, avatarYear } = Route.useLoaderData();
  const yearStaleTime = staleTimeForYear(year);

  const { data: team } = useSuspenseQuery(
    getTeamOptions({ path: { team_key: teamKey } }),
  );
  const mediaQuery = useQuery({
    ...getTeamMediaByYearOptions({ path: { team_key: teamKey, year } }),
    staleTime: yearStaleTime,
  });
  const media = useMemo(() => mediaQuery.data ?? [], [mediaQuery.data]);
  const avatarMediaQuery = useQuery({
    ...getTeamMediaByYearOptions({
      path: { team_key: teamKey, year: avatarYear },
    }),
    staleTime: staleTimeForYear(avatarYear),
  });
  const socialsQuery = useQuery(
    getTeamSocialMediaOptions({ path: { team_key: teamKey } }),
  );
  const socials = socialsQuery.data ?? [];
  const yearsParticipatedQuery = useQuery(
    getTeamYearsParticipatedOptions({ path: { team_key: teamKey } }),
  );
  const yearsParticipated = (yearsParticipatedQuery.data ?? []).toSorted(
    (a, b) => b - a,
  );
  const eventsQuery = useQuery({
    ...getTeamEventsByYearOptions({ path: { team_key: teamKey, year } }),
    staleTime: yearStaleTime,
  });
  const events = useMemo(() => eventsQuery.data ?? [], [eventsQuery.data]);
  const matchesQuery = useQuery({
    ...getTeamMatchesByYearOptions({ path: { team_key: teamKey, year } }),
    staleTime: yearStaleTime,
  });
  const matches = matchesQuery.data ?? [];
  const statusesQuery = useQuery({
    ...getTeamEventsStatusesByYearOptions({
      path: { team_key: teamKey, year },
    }),
    staleTime: yearStaleTime,
  });
  const statuses = statusesQuery.data ?? {};
  const awardsQuery = useQuery({
    ...getTeamAwardsByYearOptions({ path: { team_key: teamKey, year } }),
    staleTime: yearStaleTime,
  });
  const awards = awardsQuery.data ?? [];
  const districtsQuery = useQuery(
    getTeamDistrictsOptions({ path: { team_key: teamKey } }),
  );
  const districts = districtsQuery.data ?? [];

  const currentDistrict = districts.find((d) => d.year === year);

  const { data: districtRankings } = useQuery({
    ...getDistrictRankingsOptions({
      path: { district_key: currentDistrict?.key ?? '' },
    }),
    staleTime: yearStaleTime,
    enabled: !!currentDistrict,
  });

  const teamDistrictRanking = districtRankings?.find(
    (r) => r.team_key === teamKey,
  );

  const { data: regionalRankings } = useQuery({
    ...getRegionalRankingsOptions({ path: { year } }),
    staleTime: yearStaleTime,
    enabled: !currentDistrict,
  });

  const teamRegionalRanking = regionalRankings?.find(
    (r) => r.team_key === teamKey,
  );

  const hasRegionalEvents = events.some(
    (e) => e.event_type === EventType.REGIONAL,
  );

  const { data: regionalAdvancement } = useQuery({
    ...getRegionalAdvancementOptions({ path: { year } }),
    staleTime: yearStaleTime,
    enabled: hasRegionalEvents,
  });

  const teamRegionalAdvancement: RegionalAdvancement | undefined =
    regionalAdvancement?.[teamKey];

  // sort BEFORE launching queries that depend on it
  const sortedEvents = useMemo(
    () => events.toSorted(sortEventsComparator),
    [events],
  );

  const eventDistrictPtsQueries = useQueries({
    queries: sortedEvents.map((e) => ({
      ...getEventDistrictPointsOptions({ path: { event_key: e.key } }),
      staleTime: yearStaleTime,
      enabled: DISTRICT_EVENT_TYPES.has(e.event_type),
    })),
    combine: (results) =>
      Object.fromEntries(
        results.map((result, index) => [
          sortedEvents[index].key,
          result.data ?? null,
        ]),
      ),
  });
  const regionalPoolPtsQueries = useQueries({
    queries: sortedEvents.map((e) => ({
      ...getRegionalChampsPoolPointsOptions({ path: { event_key: e.key } }),
      staleTime: yearStaleTime,
      enabled: e.event_type === EventType.REGIONAL,
    })),
    combine: (results) =>
      Object.fromEntries(
        results.map((result, index) => [
          sortedEvents[index].key,
          result.data ?? null,
        ]),
      ),
  });
  const eventAlliancesQueries = useQueries({
    queries: sortedEvents.map((e) => ({
      ...getEventAlliancesOptions({ path: { event_key: e.key } }),
      staleTime: yearStaleTime,
    })),
    combine: (results) =>
      Object.fromEntries(
        results.map((result, index) => [
          sortedEvents[index].key,
          result.data ?? null,
        ]),
      ),
  });
  const remappedRobotKeys = sortedEvents.flatMap((e) =>
    getRemappedRobots(e, teamKey).map((r) => ({ eventKey: e.key, ...r })),
  );
  const remappedEventKeys = [
    ...new Set(remappedRobotKeys.map((r) => r.eventKey)),
  ];
  const remappedEventMatches = useQueries({
    queries: remappedEventKeys.map((eventKey) => ({
      ...getEventMatchesOptions({ path: { event_key: eventKey } }),
      staleTime: yearStaleTime,
    })),
    combine: (results) =>
      Object.fromEntries(
        results.map((result, index) => [
          remappedEventKeys[index],
          result.data ?? [],
        ]),
      ),
  });
  const remappedEventAwards = useQueries({
    queries: remappedEventKeys.map((eventKey) => ({
      ...getEventAwardsOptions({ path: { event_key: eventKey } }),
      staleTime: yearStaleTime,
    })),
    combine: (results) =>
      Object.fromEntries(
        results.map((result, index) => [
          remappedEventKeys[index],
          result.data ?? [],
        ]),
      ),
  });
  const remappedStatuses = useQueries({
    queries: remappedRobotKeys.map((r) => ({
      ...getTeamEventStatusOptions({
        path: { team_key: r.sourceTeamKey, event_key: r.eventKey },
      }),
      staleTime: yearStaleTime,
    })),
    combine: (results) => results.map((result) => result.data ?? null),
  });
  const remappedRobotsByEvent: Record<string, RobotAppearance[]> = {};
  remappedRobotKeys.forEach((r, index) => {
    (remappedRobotsByEvent[r.eventKey] ??= []).push({
      robotKey: r.robotKey,
      sourceTeamKey: r.sourceTeamKey,
      status: remappedStatuses[index],
      matches: remappedEventMatches[r.eventKey].filter((m) =>
        [...m.alliances.red.team_keys, ...m.alliances.blue.team_keys].includes(
          r.robotKey,
        ),
      ),
      awards: remappedEventAwards[r.eventKey].filter((a) =>
        a.recipient_list.some((recipient) => recipient.team_key === r.robotKey),
      ),
    });
  });

  const [inView, setInView] = useState(new Set<string>());

  const robotPics = useMemo(() => getImageMedia(media), [media]);
  const embedMedia = useMemo(() => getEmbedMedia(media), [media]);

  const maybeAvatar = useMemo(
    () =>
      avatarMediaQuery.data?.find((m): m is MediaAvatar => m.type === 'avatar'),
    [avatarMediaQuery.data],
  );

  const blueBannerAwards = awards.filter(
    (a) =>
      BLUE_BANNER_AWARDS.has(a.award_type) &&
      sortedEvents.some(
        (e) => e.key === a.event_key && SEASON_EVENT_TYPES.has(e.event_type),
      ),
  );

  const tocItems = useMemo(
    () => [
      { slug: 'team-info', label: 'Team Info' },
      ...sortedEvents.map((e) => ({
        slug: e.key,
        label: e.short_name?.trim() ? e.short_name : e.name,
      })),
    ],
    [sortedEvents],
  );

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <TableOfContents tocItems={tocItems} inView={inView}>
        <YearSelector
          currentLabel={String(year)}
          triggerClassName="w-[180px]"
          options={[
            {
              label: 'History',
              to: `/team/${team.team_number}/history`,
            },
            {
              label: 'Stats',
              to: `/team/${team.team_number}/stats`,
            },
            ...yearsParticipated.map((y) => ({
              label: String(y),
              to: `/team/${team.team_number}/${y}`,
              isCurrent: y === year,
            })),
          ]}
        />
      </TableOfContents>

      <div className="mt-8 w-full">
        <TableOfContentsSection id="team-info" setInView={setInView}>
          <div
            className="flex flex-wrap justify-center sm:flex-nowrap
              sm:justify-between"
          >
            <div className="flex flex-col justify-between">
              <div>
                <TeamPageTeamInfo
                  team={team}
                  socials={socials}
                  maybeAvatar={maybeAvatar}
                  district={districts.find((d) => d.year === year)}
                  favoriteButton={
                    <FavoriteButton
                      modelKey={teamKey}
                      modelType={MODEL_TYPE.TEAM}
                    />
                  }
                />
              </div>
            </div>
            <div className="flex-none">
              <TeamRobotPicsCarousel
                key={`${teamKey}-${year}`}
                media={robotPics}
              />
            </div>
          </div>

          <StatsSection
            events={sortedEvents}
            team={team}
            matches={matches}
            year={year}
            district={currentDistrict}
            districtRanking={teamDistrictRanking}
            regionalRanking={teamRegionalRanking}
            remappedRobots={Object.values(remappedRobotsByEvent).flat()}
          />

          {blueBannerAwards.length > 0 && (
            <>
              <Separator className="my-4" />
              <div
                data-testid="blue-banners"
                className="flex flex-row justify-around"
              >
                <BlueBanners awards={blueBannerAwards} events={sortedEvents} />
              </div>
            </>
          )}
        </TableOfContentsSection>

        <div>
          <Separator className="mt-4 mb-8" />

          {sortedEvents.map((e) => (
            <TableOfContentsSection
              key={e.key}
              id={e.key}
              setInView={setInView}
            >
              <TeamEventAppearance
                event={e}
                matches={matches.filter((m) => m.event_key === e.key)}
                status={statuses[e.key]}
                team={team}
                awards={awards.filter((a) => a.event_key === e.key)}
                maybeDistrictPoints={eventDistrictPtsQueries[e.key]}
                maybeRegionalPoolPoints={regionalPoolPtsQueries[e.key]}
                maybeAlliances={eventAlliancesQueries[e.key]}
                teamRegionalAdvancement={teamRegionalAdvancement}
                remappedRobots={remappedRobotsByEvent[e.key]}
              />
              <Separator className="my-4" />
            </TableOfContentsSection>
          ))}

          <div>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Media</h2>
              <Link
                to="/suggest/team/media"
                search={{ team_key: teamKey, year }}
                className="text-sm text-muted-foreground underline-offset-4
                  hover:underline"
              >
                Add Media
              </Link>
            </div>
            {embedMedia.length > 0 && <TeamMediaGallery media={media} />}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatsSection({
  events,
  team,
  matches,
  year,
  district,
  districtRanking,
  regionalRanking,
  remappedRobots,
}: {
  events: Event[];
  team: Team;
  matches: Match[];
  year: number;
  district?: District;
  districtRanking?: DistrictRanking;
  regionalRanking?: RegionalRanking;
  remappedRobots: RobotAppearance[];
}) {
  const officialEvents = events.filter((e) =>
    SEASON_EVENT_TYPES.has(e.event_type),
  );
  const unofficialEvents = events.filter(
    (e) => !SEASON_EVENT_TYPES.has(e.event_type),
  );

  const officialMatches = useMemo(
    () =>
      matches.filter((m) =>
        officialEvents.map((e) => e.key).includes(m.event_key),
      ),
    [matches, officialEvents],
  );

  const unofficialMatches = useMemo(
    () =>
      matches.filter((m) =>
        unofficialEvents.map((e) => e.key).includes(m.event_key),
      ),
    [matches, unofficialEvents],
  );

  const officialRecords = useMemo(
    () => calculateTeamRecordsFromMatches(team.key, officialMatches),
    [team.key, officialMatches],
  );

  const unofficialRecords = useMemo(
    () => calculateTeamRecordsFromMatches(team.key, unofficialMatches),
    [team.key, unofficialMatches],
  );
  const officialQuals = officialRecords.quals;
  const officialPlayoff = officialRecords.playoff;
  const unofficialQuals = unofficialRecords.quals;
  const unofficialPlayoff = unofficialRecords.playoff;

  const officialRecord = addRecords(officialQuals, officialPlayoff);
  const unofficialRecord = addRecords(
    addRecords(unofficialQuals, unofficialPlayoff),
    calculateRobotsRecord(remappedRobots),
  );
  const hasUnofficialMatches = hasAnyMatches(unofficialRecord);

  if (matches.length === 0) {
    return null;
  }

  return (
    <>
      <Separator className="my-4" />
      <div className="">
        Team {team.team_number} was{' '}
        <span className="font-semibold">
          {officialRecord.wins}-{officialRecord.losses}
          {officialRecord.ties > 0 ? `-${officialRecord.ties}` : ''}
        </span>{' '}
        {hasUnofficialMatches ? (
          <>
            in official play and{' '}
            <span className="font-semibold">
              {officialRecord.wins + unofficialRecord.wins}-
              {officialRecord.losses + unofficialRecord.losses}
              {officialRecord.ties + unofficialRecord.ties > 0
                ? `-${officialRecord.ties + unofficialRecord.ties}`
                : ''}
            </span>{' '}
            overall in {year}.
          </>
        ) : (
          <>overall in {year}.</>
        )}
        {district && districtRanking && (
          <>
            {' '}
            In the{' '}
            <DistrictLink
              districtAbbreviation={district.abbreviation}
              year={year}
              className="underline"
            >
              {district.display_name} district
            </DistrictLink>
            , they ranked{' '}
            <span className="font-semibold">#{districtRanking.rank}</span> with{' '}
            <span className="font-semibold">{districtRanking.point_total}</span>{' '}
            points.
          </>
        )}
        {!district && regionalRanking && (
          <>
            {' '}
            In the{' '}
            <Link
              to="/events/regional/{-$year}"
              params={{ year: String(year) }}
              className="underline"
            >
              regional pool
            </Link>
            , they ranked{' '}
            <span className="font-semibold">#{regionalRanking.rank}</span> with{' '}
            <span className="font-semibold">{regionalRanking.point_total}</span>{' '}
            points.
          </>
        )}
      </div>
    </>
  );
}

function BlueBanners({ awards, events }: { awards: Award[]; events: Event[] }) {
  return (
    <div className="flex flex-row flex-wrap justify-center gap-2">
      {sortAwardsByEventDate(awards, events).map((a) => (
        <AwardBanner
          key={`${a.award_type}-${a.event_key}`}
          award={a}
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          event={events.find((e) => e.key === a.event_key)!}
        />
      ))}
    </div>
  );
}
