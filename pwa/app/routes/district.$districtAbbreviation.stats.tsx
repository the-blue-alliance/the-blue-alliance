import { createFileRoute, notFound, useNavigate } from '@tanstack/react-router';
import { type ReactNode, useMemo } from 'react';

import {
  Award,
  Event,
  getDistrictAwards,
  getDistrictEvents,
  getDistrictHistory,
  getDistrictInsights,
} from '~/api/tba/read';
import {
  Leaderboard,
  type LeaderboardRanking,
} from '~/components/tba/leaderboard';
import { EventLink } from '~/components/tba/links';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { AwardType, BLUE_BANNER_AWARDS } from '~/lib/api/AwardType';
import { EventType } from '~/lib/api/EventType';
import { publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/district/$districtAbbreviation/stats')({
  loader: async ({ params }) => {
    const [historyResult, insightsResult] = await Promise.all([
      getDistrictHistory({
        path: { district_abbreviation: params.districtAbbreviation },
      }),
      getDistrictInsights({
        path: { district_abbreviation: params.districtAbbreviation },
      }),
    ]);

    if (historyResult.data === undefined || insightsResult.data === undefined) {
      throw notFound();
    }

    const history = historyResult.data;
    const insights = insightsResult.data;

    // Fetch events and awards for each year in parallel
    const yearResults = await Promise.all(
      history.map(async (district) => {
        const [eventsResult, awardsResult] = await Promise.all([
          getDistrictEvents({
            path: { district_key: district.key },
          }),
          getDistrictAwards({
            path: { district_key: district.key },
          }),
        ]);
        return {
          year: district.year,
          events: eventsResult.data ?? [],
          awards: awardsResult.data ?? [],
        };
      }),
    );

    return {
      abbreviation: params.districtAbbreviation,
      history,
      insights,
      yearResults,
    };
  },
  headers: publicCacheControlHeaders(),
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [
          { title: 'District Stats - The Blue Alliance' },
          {
            name: 'description',
            content: 'District stats for the FIRST Robotics Competition.',
          },
        ],
      };
    }

    return {
      meta: [
        {
          title: `${loaderData.history[loaderData.history.length - 1].display_name} District Stats - The Blue Alliance`,
        },
        {
          name: 'description',
          content: `All-time stats for the ${loaderData.history[loaderData.history.length - 1].display_name} District.`,
        },
      ],
    };
  },
  component: DistrictStatsPage,
});

function buildEventNameLookup(
  yearResults: Array<{ events: Event[] }>,
): Map<string, string> {
  const lookup = new Map<string, string>();
  for (const { events } of yearResults) {
    for (const event of events) {
      const displayName =
        event.year.toString() +
        ' ' +
        (event.short_name !== null && event.short_name?.trim() !== ''
          ? event.short_name
          : event.name);
      lookup.set(event.key, displayName);
    }
  }
  return lookup;
}

function buildContextTooltipMap(
  teamEventKeys: Map<string, string[]>,
  eventNameLookup: Map<string, string>,
): Record<string, ReactNode> {
  const map: Record<string, ReactNode> = {};
  for (const [teamKey, eventKeys] of teamEventKeys.entries()) {
    const uniqueKeys = Array.from(new Set(eventKeys));
    if (uniqueKeys.length === 0) continue;
    map[teamKey] = (
      <div className="flex flex-col gap-0.5">
        {uniqueKeys.map((eventKey) => {
          const name = eventNameLookup.get(eventKey) ?? eventKey;
          return (
            <EventLink
              key={eventKey}
              eventOrKey={eventKey}
              className="underline-offset-2 hover:underline"
            >
              {name}
            </EventLink>
          );
        })}
      </div>
    );
  }
  return map;
}

function mapToRankings(map: Map<string, number>): LeaderboardRanking[] {
  // Group keys by value
  const valueToKeys = new Map<number, string[]>();
  for (const [key, value] of map.entries()) {
    if (value <= 0) continue;
    const existing = valueToKeys.get(value);
    if (existing) {
      existing.push(key);
    } else {
      valueToKeys.set(value, [key]);
    }
  }
  // Sort by value descending, keys sorted by team number
  return Array.from(valueToKeys.entries())
    .sort(([a], [b]) => b - a)
    .map(([value, keys]) => ({
      value,
      keys: keys.sort(
        (a, b) => parseInt(a.substring(3)) - parseInt(b.substring(3)),
      ),
    }));
}

function computeLeaderboards(
  teamData: Record<
    string,
    {
      cmp_appearances: number;
      dcmp_appearances: number;
      dcmp_wins: number;
      district_event_wins: number;
      total_matches_played: number;
      team_awards: number;
      district_seasons: number;
    }
  > | null,
  yearResults: Array<{
    year: number;
    events: Event[];
    awards: Award[];
  }>,
) {
  // Stats from team_data (insight API)
  const cmpAppearances = new Map<string, number>();
  const dcmpAppearances = new Map<string, number>();
  const dcmpWins = new Map<string, number>();
  const districtEventWins = new Map<string, number>();
  const mostMatchesPlayed = new Map<string, number>();
  const mostAwards = new Map<string, number>();
  const eventsAttended = new Map<string, number>();

  if (teamData) {
    for (const [teamKey, data] of Object.entries(teamData)) {
      if (data.cmp_appearances > 0) {
        cmpAppearances.set(teamKey, data.cmp_appearances);
      }
      if (data.dcmp_appearances > 0) {
        dcmpAppearances.set(teamKey, data.dcmp_appearances);
      }
      if (data.dcmp_wins > 0) {
        dcmpWins.set(teamKey, data.dcmp_wins);
      }
      if (data.district_event_wins > 0) {
        districtEventWins.set(teamKey, data.district_event_wins);
      }
      if (data.total_matches_played > 0) {
        mostMatchesPlayed.set(teamKey, data.total_matches_played);
      }
      if (data.team_awards > 0) {
        mostAwards.set(teamKey, data.team_awards);
      }
      if (data.district_seasons > 0) {
        eventsAttended.set(teamKey, data.district_seasons);
      }
    }
  }

  const eventNameLookup = buildEventNameLookup(yearResults);

  // Computed stats from awards + events data
  const dcmpFinalsAppearances = new Map<string, number>();
  const districtEventFinalsAppearances = new Map<string, number>();
  const blueBanners = new Map<string, number>();
  const impactWins = new Map<string, number>();
  const dcmpImpactWins = new Map<string, number>();
  const eiWins = new Map<string, number>();
  const dcmpEiWins = new Map<string, number>();
  const leadershipWins = new Map<string, number>();
  const wffaWins = new Map<string, number>();

  // Track event keys for tooltip context
  const blueBannerEvents = new Map<string, string[]>();
  const impactEvents = new Map<string, string[]>();
  const dcmpImpactEvents = new Map<string, string[]>();
  const eiEvents = new Map<string, string[]>();
  const dcmpEiEvents = new Map<string, string[]>();
  const leadershipEvents = new Map<string, string[]>();
  const wffaEvents = new Map<string, string[]>();

  for (const { events, awards } of yearResults) {
    const dcmpEventKeys = new Set(
      events
        .filter(
          (e) =>
            e.event_type === EventType.DISTRICT_CMP ||
            e.event_type === EventType.DISTRICT_CMP_DIVISION,
        )
        .map((e) => e.key),
    );

    const districtEventKeys = new Set(
      events
        .filter((e) => e.event_type === EventType.DISTRICT)
        .map((e) => e.key),
    );

    for (const award of awards) {
      for (const recipient of award.recipient_list) {
        const teamKey = recipient.team_key;
        if (!teamKey) continue;

        // DCMP finals appearances (finalist at DCMP)
        if (
          (award.award_type === AwardType.FINALIST ||
            award.award_type === AwardType.WINNER) &&
          dcmpEventKeys.has(award.event_key)
        ) {
          dcmpFinalsAppearances.set(
            teamKey,
            (dcmpFinalsAppearances.get(teamKey) ?? 0) + 1,
          );
        }

        // District event finals appearances (finalist at district events)
        if (
          (award.award_type === AwardType.FINALIST ||
            award.award_type === AwardType.WINNER) &&
          districtEventKeys.has(award.event_key)
        ) {
          districtEventFinalsAppearances.set(
            teamKey,
            (districtEventFinalsAppearances.get(teamKey) ?? 0) + 1,
          );
        }

        // Blue banners
        if (BLUE_BANNER_AWARDS.has(award.award_type)) {
          blueBanners.set(teamKey, (blueBanners.get(teamKey) ?? 0) + 1);
          const bb = blueBannerEvents.get(teamKey) ?? [];
          bb.push(award.event_key);
          blueBannerEvents.set(teamKey, bb);
        }

        // Impact/Chairman's wins
        if (award.award_type === AwardType.CHAIRMANS) {
          impactWins.set(teamKey, (impactWins.get(teamKey) ?? 0) + 1);
          const ev = impactEvents.get(teamKey) ?? [];
          ev.push(award.event_key);
          impactEvents.set(teamKey, ev);
        }

        // DCMPImpact/Chairman's wins
        if (
          award.award_type === AwardType.CHAIRMANS &&
          dcmpEventKeys.has(award.event_key)
        ) {
          dcmpImpactWins.set(teamKey, (dcmpImpactWins.get(teamKey) ?? 0) + 1);
          const ev = dcmpImpactEvents.get(teamKey) ?? [];
          ev.push(award.event_key);
          dcmpImpactEvents.set(teamKey, ev);
        }

        // Engineering Inspiration wins
        if (award.award_type === AwardType.ENGINEERING_INSPIRATION) {
          eiWins.set(teamKey, (eiWins.get(teamKey) ?? 0) + 1);
          const ev = eiEvents.get(teamKey) ?? [];
          ev.push(award.event_key);
          eiEvents.set(teamKey, ev);
        }

        // DCMP Engineering Inspiration wins
        if (
          award.award_type === AwardType.ENGINEERING_INSPIRATION &&
          dcmpEventKeys.has(award.event_key)
        ) {
          dcmpEiWins.set(teamKey, (dcmpEiWins.get(teamKey) ?? 0) + 1);
          const ev = dcmpEiEvents.get(teamKey) ?? [];
          ev.push(award.event_key);
          dcmpEiEvents.set(teamKey, ev);
        }

        // Leadership wins
        if (award.award_type === AwardType.DEANS_LIST) {
          leadershipWins.set(teamKey, (leadershipWins.get(teamKey) ?? 0) + 1);
          const ev = leadershipEvents.get(teamKey) ?? [];
          ev.push(award.event_key);
          leadershipEvents.set(teamKey, ev);
        }

        // WFFA wins
        if (award.award_type === AwardType.WOODIE_FLOWERS) {
          wffaWins.set(teamKey, (wffaWins.get(teamKey) ?? 0) + 1);
          const ev = wffaEvents.get(teamKey) ?? [];
          ev.push(award.event_key);
          wffaEvents.set(teamKey, ev);
        }
      }
    }
  }

  return {
    cmpAppearances: mapToRankings(cmpAppearances),
    dcmpAppearances: mapToRankings(dcmpAppearances),
    dcmpFinalsAppearances: mapToRankings(dcmpFinalsAppearances),
    dcmpWins: mapToRankings(dcmpWins),
    eventsAttended: mapToRankings(eventsAttended),
    districtEventFinalsAppearances: mapToRankings(
      districtEventFinalsAppearances,
    ),
    districtEventWins: mapToRankings(districtEventWins),
    blueBanners: mapToRankings(blueBanners),
    mostMatchesPlayed: mapToRankings(mostMatchesPlayed),
    mostAwards: mapToRankings(mostAwards),
    impactWins: mapToRankings(impactWins),
    dcmpImpactWins: mapToRankings(dcmpImpactWins),
    eiWins: mapToRankings(eiWins),
    dcmpEiWins: mapToRankings(dcmpEiWins),
    leadershipWins: mapToRankings(leadershipWins),
    wffaWins: mapToRankings(wffaWins),
    // Tooltip maps
    blueBannerTooltips: buildContextTooltipMap(
      blueBannerEvents,
      eventNameLookup,
    ),
    impactTooltips: buildContextTooltipMap(impactEvents, eventNameLookup),
    dcmpImpactTooltips: buildContextTooltipMap(
      dcmpImpactEvents,
      eventNameLookup,
    ),
    eiTooltips: buildContextTooltipMap(eiEvents, eventNameLookup),
    dcmpEiTooltips: buildContextTooltipMap(dcmpEiEvents, eventNameLookup),
    leadershipTooltips: buildContextTooltipMap(
      leadershipEvents,
      eventNameLookup,
    ),
    wffaTooltips: buildContextTooltipMap(wffaEvents, eventNameLookup),
  };
}

interface PerAwardLeaderboard {
  awardType: AwardType;
  isDcmp: boolean;
  name: string;
  rankings: LeaderboardRanking[];
  contextTooltipMap: Record<string, ReactNode>;
}

function computePerAwardLeaderboards(
  yearResults: Array<{
    year: number;
    events: Event[];
    awards: Award[];
  }>,
): PerAwardLeaderboard[] {
  const eventNameLookup = buildEventNameLookup(yearResults);

  // Awards that progress from district events to DCMP — track separately
  const DCMP_PROGRESSION_AWARDS = new Set([
    AwardType.CHAIRMANS,
    AwardType.DEANS_LIST,
    AwardType.ENGINEERING_INSPIRATION,
    AwardType.ROOKIE_ALL_STAR,
  ]);

  // For each award_type, track: team -> count, team -> event keys, and the most recent name
  // For progression awards, use separate "dcmp_" prefixed keys
  const awardTeamCounts = new Map<string, Map<string, number>>();
  const awardTeamEventKeys = new Map<string, Map<string, string[]>>();
  const awardNames = new Map<string, { name: string; year: number }>();
  const awardTypeMap = new Map<string, AwardType>();

  for (const { events, awards } of yearResults) {
    const dcmpEventKeys = new Set(
      events
        .filter(
          (e) =>
            e.event_type === EventType.DISTRICT_CMP ||
            e.event_type === EventType.DISTRICT_CMP_DIVISION,
        )
        .map((e) => e.key),
    );

    for (const award of awards) {
      // Skip Winner/Finalist — already covered in other tabs
      if (
        award.award_type === AwardType.WINNER ||
        award.award_type === AwardType.FINALIST
      ) {
        continue;
      }

      const isDcmpAward = dcmpEventKeys.has(award.event_key);
      const hasProgression = DCMP_PROGRESSION_AWARDS.has(award.award_type);

      // For progression awards, use separate keys for district vs DCMP
      const leaderboardKey =
        hasProgression && isDcmpAward
          ? `dcmp_${award.award_type}`
          : `${award.award_type}`;

      awardTypeMap.set(leaderboardKey, award.award_type);

      // Track the most recent name for this leaderboard
      const existing = awardNames.get(leaderboardKey);
      if (!existing || award.year > existing.year) {
        let displayName: string;
        if (award.award_type === AwardType.DEANS_LIST) {
          displayName = isDcmpAward
            ? "Dean's List Finalist Award"
            : "Dean's List Semi-Finalist Award";
        } else if (hasProgression && isDcmpAward) {
          displayName = award.name.startsWith('District Championship')
            ? award.name
            : 'District Championship ' + award.name;
        } else {
          displayName = award.name;
        }
        awardNames.set(leaderboardKey, {
          name: displayName,
          year: award.year,
        });
      }

      for (const recipient of award.recipient_list) {
        const teamKey = recipient.team_key;
        if (!teamKey) continue;

        let teamCounts = awardTeamCounts.get(leaderboardKey);
        if (!teamCounts) {
          teamCounts = new Map<string, number>();
          awardTeamCounts.set(leaderboardKey, teamCounts);
        }
        teamCounts.set(teamKey, (teamCounts.get(teamKey) ?? 0) + 1);

        let teamEvents = awardTeamEventKeys.get(leaderboardKey);
        if (!teamEvents) {
          teamEvents = new Map<string, string[]>();
          awardTeamEventKeys.set(leaderboardKey, teamEvents);
        }
        const ev = teamEvents.get(teamKey) ?? [];
        ev.push(award.event_key);
        teamEvents.set(teamKey, ev);
      }
    }
  }

  // Build leaderboards, sorted by SORT_ORDER then award name
  const leaderboards: PerAwardLeaderboard[] = [];
  for (const [leaderboardKey, teamCounts] of awardTeamCounts.entries()) {
    const awardType = awardTypeMap.get(leaderboardKey) ?? AwardType.OTHER;
    const name = awardNames.get(leaderboardKey)?.name ?? `Award ${awardType}`;
    const rankings = mapToRankings(teamCounts);
    if (rankings.length > 0) {
      const teamEvents =
        awardTeamEventKeys.get(leaderboardKey) ?? new Map<string, string[]>();
      leaderboards.push({
        awardType,
        isDcmp: leaderboardKey.startsWith('dcmp_'),
        name,
        rankings,
        contextTooltipMap: buildContextTooltipMap(teamEvents, eventNameLookup),
      });
    }
  }

  leaderboards.sort((a, b) => {
    // Custom display order overrides (lower = earlier)
    const displayOrder = (at: AwardType) => {
      if (at === AwardType.DEANS_LIST) return 3;
      if (at === AwardType.WOODIE_FLOWERS) return 4;
      return at;
    };
    const aOrder = displayOrder(a.awardType);
    const bOrder = displayOrder(b.awardType);
    if (aOrder !== bOrder) return aOrder - bOrder;
    if (a.isDcmp !== b.isDcmp) return a.isDcmp ? 1 : -1;
    return 0;
  });

  return leaderboards;
}

function DistrictStatsPage() {
  const { abbreviation, history, insights, yearResults } =
    Route.useLoaderData();
  const navigate = useNavigate();

  const validYears = history.map((d) => d.year).sort((a, b) => b - a);

  const leaderboards = useMemo(
    () => computeLeaderboards(insights.team_data, yearResults),
    [insights.team_data, yearResults],
  );

  const perAwardLeaderboards = useMemo(
    () => computePerAwardLeaderboards(yearResults),
    [yearResults],
  );

  const displayName = history[history.length - 1].display_name;

  return (
    <div>
      <div className="mt-4 flex items-center justify-between gap-4">
        <h1 className="text-4xl font-medium">{displayName} Stats</h1>
        <Select
          onValueChange={(value) => {
            if (value === 'stats') return;
            void navigate({
              to: '/district/$districtAbbreviation/{-$year}',
              params: {
                districtAbbreviation: abbreviation,
                year: value,
              },
            });
          }}
        >
          <SelectTrigger className="w-30">
            <SelectValue placeholder="Stats" />
          </SelectTrigger>
          <SelectContent className="max-h-[30vh] overflow-y-auto">
            <SelectItem value="stats">Stats</SelectItem>
            {validYears.map((y) => (
              <SelectItem key={y} value={`${y}`}>
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="championships" className="mt-4">
        <TabsList
          className="flex h-auto flex-wrap items-center justify-evenly
            *:basis-1/2 lg:*:basis-1"
        >
          <TabsTrigger value="championships">Championships</TabsTrigger>
          <TabsTrigger value="events">Events</TabsTrigger>
          <TabsTrigger value="awards">Awards</TabsTrigger>
        </TabsList>

        <TabsContent value="championships">
          <div className="grid gap-6 lg:grid-cols-2">
            <Leaderboard
              title="Most Championship Appearances"
              rankings={leaderboards.cmpAppearances}
              keyType="team"
              year={0}
            />
            <Leaderboard
              title="Most District Championship Appearances"
              rankings={leaderboards.dcmpAppearances}
              keyType="team"
              year={0}
            />
            <Leaderboard
              title="Most District Championship Finals Appearances"
              rankings={leaderboards.dcmpFinalsAppearances}
              keyType="team"
              year={0}
            />
            <Leaderboard
              title="Most District Championship Wins"
              rankings={leaderboards.dcmpWins}
              keyType="team"
              year={0}
            />
          </div>
        </TabsContent>

        <TabsContent value="events">
          <div className="grid gap-6 lg:grid-cols-2">
            <Leaderboard
              title="Most District Seasons"
              rankings={leaderboards.eventsAttended}
              keyType="team"
              year={0}
            />
            <Leaderboard
              title="Most District Event Finals Appearances"
              rankings={leaderboards.districtEventFinalsAppearances}
              keyType="team"
              year={0}
            />
            <Leaderboard
              title="Most District Event Wins"
              rankings={leaderboards.districtEventWins}
              keyType="team"
              year={0}
            />
            <Leaderboard
              title="Most District Matches Played"
              rankings={leaderboards.mostMatchesPlayed}
              keyType="team"
              year={0}
            />
          </div>
        </TabsContent>

        <TabsContent value="awards">
          <div className="grid gap-6 lg:grid-cols-2">
            <Leaderboard
              title="Most District Blue Banners"
              rankings={leaderboards.blueBanners}
              keyType="team"
              year={0}
              contextTooltipMap={leaderboards.blueBannerTooltips}
            />
            <Leaderboard
              title="Most District Awards"
              rankings={leaderboards.mostAwards}
              keyType="team"
              year={0}
            />
            {perAwardLeaderboards.map((lb) => (
              <Leaderboard
                key={lb.name}
                title={`Most ${lb.name} Wins`}
                rankings={lb.rankings}
                keyType="team"
                year={0}
                contextTooltipMap={lb.contextTooltipMap}
              />
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
