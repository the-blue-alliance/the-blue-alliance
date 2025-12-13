import { createFileRoute, notFound, useNavigate } from '@tanstack/react-router';

import { getTeamsSimple } from '~/api/tba/read';
import { getStatusOptions } from '~/api/tba/read/@tanstack/react-query.gen';
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
  loader: async ({ params, context: { queryClient } }) => {
    const status = await queryClient.ensureQueryData(getStatusOptions({}));

    const maxPageNum = Math.floor(status.max_team_page / 2) + 1;
    const pageNum = parseParamsForTeamPgNumElseDefault(params, maxPageNum);

    if (pageNum === undefined) {
      throw notFound();
    }

    const [teamsSetOne, teamsSetTwo] = await Promise.all([
      getTeamsSimple({ path: { page_num: 2 * (pageNum - 1) } }),
      getTeamsSimple({ path: { page_num: 2 * (pageNum - 1) + 1 } }),
    ]);
    if (teamsSetOne.data === undefined || teamsSetTwo.data === undefined) {
      throw new Error('Failed to load teams');
    }
    const teams = teamsSetOne.data.concat(teamsSetTwo.data);

    return { teams, pageNum, maxPageNum };
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
  const { teams, pageNum, maxPageNum } = Route.useLoaderData();
  const navigate = useNavigate();

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <div className="basis-full lg:basis-1/6">
        <div className="top-14 pt-8 lg:sticky">
          <Select
            value={pageNum.toString()}
            onValueChange={(value) => {
              void navigate({
                to: '/teams/{-$pgNum}',
                params: { pgNum: value },
              });
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder={pageNum} />
            </SelectTrigger>
            <SelectContent>
              {Array.from({ length: maxPageNum }, (_, i) => {
                const p = i + 1;
                return (
                  <SelectItem key={p} value={p.toString()}>
                    {TeamPageNumberToRange(p)}
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="basis-full overflow-x-auto lg:basis-5/6 lg:py-8">
        <h1 className="mb-3 text-3xl font-medium">
          <i>FIRST</i> Robotics Teams {TeamPageNumberToRange(pageNum)}{' '}
          <small className="text-xl text-muted-foreground">
            {teams.length} Teams
          </small>
        </h1>
        <TeamListTable teams={teams} />
      </div>
    </div>
  );
}
