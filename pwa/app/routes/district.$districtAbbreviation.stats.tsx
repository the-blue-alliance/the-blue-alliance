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
import { TeamLink } from '~/components/tba/links';
import { Divider } from '~/components/ui/divider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { AwardType, BLUE_BANNER_AWARDS } from '~/lib/api/AwardType';
import { EventType } from '~/lib/api/EventType';
import { publicCacheControlHeaders } from '~/lib/utils';

interface TeamStat {
  teamKey: string;
  value: number;
}

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

function computeLeaderboards(
  teamData: Record<
    string,
    {
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
  const dcmpAppearances: TeamStat[] = [];
  const dcmpWins: TeamStat[] = [];
  const districtEventWins: TeamStat[] = [];
  const mostMatchesPlayed: TeamStat[] = [];
  const mostAwards: TeamStat[] = [];

  if (teamData) {
    for (const [teamKey, data] of Object.entries(teamData)) {
      if (data.dcmp_appearances > 0) {
        dcmpAppearances.push({ teamKey, value: data.dcmp_appearances });
      }
      if (data.dcmp_wins > 0) {
        dcmpWins.push({ teamKey, value: data.dcmp_wins });
      }
      if (data.district_event_wins > 0) {
        districtEventWins.push({ teamKey, value: data.district_event_wins });
      }
      if (data.total_matches_played > 0) {
        mostMatchesPlayed.push({ teamKey, value: data.total_matches_played });
      }
      if (data.team_awards > 0) {
        mostAwards.push({ teamKey, value: data.team_awards });
      }
    }
  }

  // Computed stats from awards + events data
  const dcmpFinalsAppearances = new Map<string, number>();
  const districtEventFinalsAppearances = new Map<string, number>();
  const blueBanners = new Map<string, number>();
  const impactWins = new Map<string, number>();
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
          award.award_type === AwardType.FINALIST &&
          dcmpEventKeys.has(award.event_key)
        ) {
          dcmpFinalsAppearances.set(
            teamKey,
            (dcmpFinalsAppearances.get(teamKey) ?? 0) + 1,
          );
        }

        // District event finals appearances (finalist at district events)
        if (
          award.award_type === AwardType.FINALIST &&
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

  // District seasons from insight team_data
  const eventsAttendedStats: TeamStat[] = [];
  if (teamData) {
    for (const [teamKey, data] of Object.entries(teamData)) {
      if (data.district_seasons > 0) {
        eventsAttendedStats.push({ teamKey, value: data.district_seasons });
      }
    }
  }

  const mapToSorted = (map: Map<string, number>): TeamStat[] =>
    Array.from(map.entries())
      .filter(([, v]) => v > 0)
      .map(([teamKey, value]) => ({ teamKey, value }))
      .sort((a, b) => b.value - a.value);

  const sortDesc = (arr: TeamStat[]) =>
    [...arr].sort((a, b) => b.value - a.value);

  return {
    dcmpAppearances: sortDesc(dcmpAppearances),
    dcmpFinalsAppearances: mapToSorted(dcmpFinalsAppearances),
    dcmpWins: sortDesc(dcmpWins),
    eventsAttended: sortDesc(eventsAttendedStats),
    districtEventFinalsAppearances: mapToSorted(districtEventFinalsAppearances),
    districtEventWins: sortDesc(districtEventWins),
    blueBanners: mapToSorted(blueBanners),
    mostMatchesPlayed: sortDesc(mostMatchesPlayed),
    mostAwards: sortDesc(mostAwards),
    impactWins: mapToSorted(impactWins),
    eiWins: mapToSorted(eiWins),
    wffaWins: mapToSorted(wffaWins),
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
      <div className="mt-4 flex items-center gap-4">
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
          <div className="space-y-8">
            <LeaderboardTable
              title="Most District Championship Appearances"
              data={leaderboards.dcmpAppearances}
              label="Appearances"
            />
            <LeaderboardTable
              title="Most District Championship Finals Appearances"
              data={leaderboards.dcmpFinalsAppearances}
              label="Finals Appearances"
            />
            <LeaderboardTable
              title="Most District Championship Wins"
              data={leaderboards.dcmpWins}
              label="Wins"
            />
          </div>
        </TabsContent>

        <TabsContent value="events">
          <div className="space-y-8">
            <LeaderboardTable
              title="Most District Seasons"
              data={leaderboards.eventsAttended}
              label="Seasons"
            />
            <LeaderboardTable
              title="Most District Event Finals Appearances"
              data={leaderboards.districtEventFinalsAppearances}
              label="Finals Appearances"
            />
            <LeaderboardTable
              title="Most District Event Wins"
              data={leaderboards.districtEventWins}
              label="Wins"
            />
            <LeaderboardTable
              title="Most Matches Played"
              data={leaderboards.mostMatchesPlayed}
              label="Matches"
            />
          </div>
        </TabsContent>

        <TabsContent value="awards">
          <div className="space-y-8">
            <LeaderboardTable
              title="Most Blue Banners"
              data={leaderboards.blueBanners}
              label="Banners"
            />
            <LeaderboardTable
              title="Most Awards"
              data={leaderboards.mostAwards}
              label="Awards"
            />
            <LeaderboardTable
              title="Most Impact Award Wins"
              data={leaderboards.impactWins}
              label="Wins"
            />
            <LeaderboardTable
              title="Most Engineering Inspiration Award Wins"
              data={leaderboards.eiWins}
              label="Wins"
            />
            <LeaderboardTable
              title="Most Woodie Flowers Finalist Award Wins"
              data={leaderboards.wffaWins}
              label="Wins"
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function LeaderboardTable({
  title,
  data,
  label,
  limit = 25,
}: {
  title: string;
  data: TeamStat[];
  label: string;
  limit?: number;
}) {
  if (data.length === 0) {
    return null;
  }

  const displayData = data.slice(0, limit);

  return (
    <div>
      <Divider className="py-4">
        <div className="text-xl">{title}</div>
      </Divider>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">Rank</TableHead>
            <TableHead>Team</TableHead>
            <TableHead className="text-right">{label}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {displayData.map((entry, index) => {
            // Compute rank accounting for ties
            const rank =
              index === 0 || displayData[index - 1].value !== entry.value
                ? index + 1
                : '';

            return (
              <TableRow key={entry.teamKey}>
                <TableCell className="tabular-nums">{rank}</TableCell>
                <TableCell>
                  <TeamLink teamOrKey={entry.teamKey}>
                    {entry.teamKey.substring(3)}
                  </TeamLink>
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {entry.value}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
