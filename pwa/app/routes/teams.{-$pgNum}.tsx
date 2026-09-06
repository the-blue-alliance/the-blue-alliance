import { useSuspenseQueries } from '@tanstack/react-query';
import { createFileRoute, notFound, useNavigate } from '@tanstack/react-router';

import { getTeamsSimpleOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import FavoriteTeamsSection from '~/components/tba/favoriteTeamsSection';
import TeamListTable from '~/components/tba/teamListTable';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import {
  parseParamsForTeamPgNumElseDefault,
  publicCacheControlHeaders,
} from '~/lib/utils';

export const Route = createFileRoute('/teams/{-$pgNum}')({
  loader: async ({ params, context: { status, queryClient } }) => {
    const maxPageNum = Math.floor(status.max_team_page / 2) + 1;
    const pageNum = parseParamsForTeamPgNumElseDefault(params, maxPageNum);

    if (pageNum === undefined) {
      throw notFound();
    }

    await Promise.all([
      queryClient.ensureQueryData(
        getTeamsSimpleOptions({ path: { page_num: 2 * (pageNum - 1) } }),
      ),
      queryClient.ensureQueryData(
        getTeamsSimpleOptions({ path: { page_num: 2 * (pageNum - 1) + 1 } }),
      ),
    ]);

    return { pageNum, maxPageNum };
  },
  headers: publicCacheControlHeaders(),
  head: () => {
    return {
      meta: [
        { title: 'FIRST Robotics Teams - The Blue Alliance' },
        {
          name: 'description',
          content: `List of teams in the FIRST Robotics Competition.`,
        },
      ],
    };
  },
  component: TeamsPage,
});

function TeamPageNumberToRange(pageNum: number): string {
  // Page number is 1-indexed
  if (pageNum === 1) {
    return '1-999';
  }
  const thousand = (pageNum - 1) % 1000;
  return `${thousand}000s`;
}

function TeamsPage() {
  const { pageNum, maxPageNum } = Route.useLoaderData();
  const navigate = useNavigate();

  const [{ data: teamsSetOne }, { data: teamsSetTwo }] = useSuspenseQueries({
    queries: [
      getTeamsSimpleOptions({ path: { page_num: 2 * (pageNum - 1) } }),
      getTeamsSimpleOptions({ path: { page_num: 2 * (pageNum - 1) + 1 } }),
    ],
  });
  const teams = teamsSetOne.concat(teamsSetTwo);

  // Base UI's Select.Value renders the raw value unless the items are
  // registered on Select.Root, so provide value -> label pairs there too.
  const pageItems = Array.from({ length: maxPageNum }, (_, i) => ({
    value: (i + 1).toString(),
    label: TeamPageNumberToRange(i + 1),
  }));

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <div className="basis-full lg:basis-1/6">
        <div className="top-14 pt-8 lg:sticky">
          <Select
            items={pageItems}
            value={pageNum.toString()}
            onValueChange={(value) => {
              if (value === null) return;
              void navigate({
                to: '/teams/{-$pgNum}',
                params: { pgNum: value },
              });
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {pageItems.map(({ value, label }) => (
                <SelectItem key={value} value={value}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="basis-full overflow-x-auto lg:basis-5/6 lg:py-8">
        {pageNum === 1 && <FavoriteTeamsSection />}
        <h1 className="mb-3 text-3xl font-medium">
          <i>FIRST</i> Robotics Teams {TeamPageNumberToRange(pageNum)}
        </h1>
        <TeamListTable teams={teams} />
      </div>
    </div>
  );
}
