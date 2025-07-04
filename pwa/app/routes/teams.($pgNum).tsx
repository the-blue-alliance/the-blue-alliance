import { useLoaderData, useNavigate } from 'react-router';

import { getStatus, getTeamsSimple } from '~/api/tba';
import TeamListTable from '~/components/tba/teamListTable';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import { parseParamsForTeamPgNumElseDefault } from '~/lib/utils';

import { Route } from '.react-router/types/app/routes/+types/teams.($pgNum)';

async function loadData(params: Route.LoaderArgs['params']) {

  //TODO: Cache
  const apiStatus = await getStatus({});

  if (apiStatus.data === undefined) {
    throw new Response(null, {
      status: 500,
      statusText: 'Server failed to report status'
    });
  }

  const maxPageNum = apiStatus.data.max_team_page;
  const pageNum = await parseParamsForTeamPgNumElseDefault(params, maxPageNum);

  if (pageNum === undefined) {
    throw new Response(null, {
      status: 404,
      statusText: 'Page Number was not specified in request',
    });
  }

  const teamsSetOne = await getTeamsSimple({ path: { page_num: pageNum } })

  if (apiStatus.data.max_team_page === 0) {
    throw new Response(null, {
      status: 404,
      statusText: 'Data for Max Team Page was missing or incorrect',
    });
  }

  if (teamsSetOne === undefined) {
    throw new Response(null, {
      status: 500,
      statusText: 'Server failed to respond with Team Data (Set 1/2)',
    });
  }

  if (teamsSetOne.data === undefined || teamsSetOne.data.length === 0) {
    throw new Response(null, {
      status: 404,
      statusText: 'Team Data (Set 1/2) was missing',
    });
  }

  let teams = teamsSetOne.data;

  if (pageNum < maxPageNum) {
    const teamsSetTwo = await getTeamsSimple({ path: { page_num: pageNum + 1 } });

    if (teamsSetTwo === undefined) {
      throw new Response(null, {
        status: 500,
        statusText: 'Server failed to respond with Team Data (Set 2/2)',
      });
    }

    if (teamsSetTwo.data === undefined || teamsSetTwo.data.length === 0) {
      throw new Response(null, {
        status: 404,
        statusText: 'Team Data (Set 2/2) was missing',
      });
    }

    teams = teamsSetOne.data.concat(teamsSetTwo.data);
  }

  return { pageNum, teams, maxPageNum };
}

export async function loader({ params }: Route.LoaderArgs) {
  return await loadData(params);
}

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return await loadData(params);
}

export function meta({ data }: Route.MetaArgs) {
  return [
    {
      title: `FIRST Robotics Teams - The Blue Alliance`,
    },
    {
      name: 'description',
      content: `List of teams in the FIRST Robotics Competition.`,
    },
  ];
}

interface EventGroup {
  groupName: string;
  slug: string;
  events: Event[];
}

function TeamPageNumberToRange(pageNum: number, maxPageNum: number): string {
  if (pageNum === 0) return '1-999';

  if (pageNum % 2 === 0) {
    let start = pageNum * 500;
    return `${start}s`;
  }

  let start = pageNum * 500;
  let end = start + (maxPageNum === pageNum ? 500 : 1000);

  return `${start}-${end}`;
}

export default function TeamsPage() {
  const { pageNum, teams, maxPageNum } = useLoaderData<typeof loader>();
  const navigate = useNavigate();

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <div className="basis-full lg:basis-1/6">
        <div className="top-14 pt-8 lg:sticky">
          <Select
            value={String(pageNum)}
            onValueChange={(value) => {
              void navigate(`/teams/${value}`);
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue
                placeholder={TeamPageNumberToRange(pageNum, maxPageNum)}
              />
            </SelectTrigger>
            <SelectContent>
              {pageNum % 2 === 1 && (
                <SelectItem key={pageNum} value={String(pageNum)}>
                  {TeamPageNumberToRange(pageNum, maxPageNum)}
                </SelectItem>
              )}

              {Array.from(
                {
                  length:
                    Math.ceil(maxPageNum / 2) + (maxPageNum % 2 === 0 ? 1 : 0),
                },
                (_, i) => i * 2,
              ).map((page) => (
                <SelectItem key={page} value={String(page)}>
                  {TeamPageNumberToRange(page, maxPageNum)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="basis-full overflow-x-auto lg:basis-5/6 lg:py-8">
        {
          <h1 className="mb-3 text-3xl font-medium">
            <em>FIRST</em> Robotics Teams{' '}
            {TeamPageNumberToRange(pageNum, maxPageNum)}{' '}
            <small className="text-xl text-slate-500">
              {teams.length} Teams
            </small>
          </h1>
        }
        <TeamListTable teams={teams} />
      </div>
    </div>
  );
}
