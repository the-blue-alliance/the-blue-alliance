import { createFileRoute, notFound, useNavigate } from '@tanstack/react-router';
import { useMemo } from 'react';

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

  // Computed stats from awards + events data
  const dcmpFinalsAppearances = new Map<string, number>();
  const districtEventFinalsAppearances = new Map<string, number>();
  const blueBanners = new Map<string, number>();
  const impactWins = new Map<string, number>();
  const dcmpImpactWins = new Map<string, number>();
  const eiWins = new Map<string, number>();
  const wffaWins = new Map<string, number>();

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
        }

        // Impact/Chairman's wins
        if (award.award_type === AwardType.CHAIRMANS) {
          impactWins.set(teamKey, (impactWins.get(teamKey) ?? 0) + 1);
        }

        // DCMPImpact/Chairman's wins
        if (
          award.award_type === AwardType.CHAIRMANS &&
          dcmpEventKeys.has(award.event_key)
        ) {
          dcmpImpactWins.set(teamKey, (dcmpImpactWins.get(teamKey) ?? 0) + 1);
        }

        // Engineering Inspiration wins
        if (award.award_type === AwardType.ENGINEERING_INSPIRATION) {
          eiWins.set(teamKey, (eiWins.get(teamKey) ?? 0) + 1);
        }

        // WFFA wins
        if (award.award_type === AwardType.WOODIE_FLOWERS) {
          wffaWins.set(teamKey, (wffaWins.get(teamKey) ?? 0) + 1);
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
    wffaWins: mapToRankings(wffaWins),
  };
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
            />
            <Leaderboard
              title="Most District Awards"
              rankings={leaderboards.mostAwards}
              keyType="team"
              year={0}
            />
            <Leaderboard
              title="Most District Impact Award Wins"
              rankings={leaderboards.impactWins}
              keyType="team"
              year={0}
            />
            <Leaderboard
              title="Most District Championship Impact Award Wins"
              rankings={leaderboards.dcmpImpactWins}
              keyType="team"
              year={0}
            />
            <Leaderboard
              title="Most District Engineering Inspiration Award Wins"
              rankings={leaderboards.eiWins}
              keyType="team"
              year={0}
            />
            <Leaderboard
              title="Most District Woodie Flowers Finalist Award Wins"
              rankings={leaderboards.wffaWins}
              keyType="team"
              year={0}
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
