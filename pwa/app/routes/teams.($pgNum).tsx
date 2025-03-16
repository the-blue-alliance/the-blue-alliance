import { useState } from 'react';
import { InView } from 'react-intersection-observer';
import { useLoaderData, useNavigate } from 'react-router';

import { TeamSimple, getTeamsSimple } from '~/api/v3';
import EventListTable from '~/components/tba/eventListTable';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import {
  parseParamsForTeamPgNumElseDefault,
  pluralize,
  slugify,
} from '~/lib/utils';

import { Route } from '.react-router/types/app/routes/+types/teams.($pgNum)';
import { i } from 'node_modules/@react-router/dev/dist/routes-DHIOx0R9';
import TeamListTable from '~/components/tba/teamListTable';

async function loadData(params: Route.LoaderArgs['params']) {
  const pageNum = await parseParamsForTeamPgNumElseDefault(params);
  
  if (pageNum === undefined) {
    throw new Response(null, {
      status: 404,
    });
  }

  const teamsSetOne = await getTeamsSimple({pageNum: pageNum}) ;

  if (teamsSetOne.status !== 200) {
    throw new Response(null, {
      status: 500,
    });
  }

  if (teamsSetOne.data.length === 0) {
    throw new Response(null, {
      status: 404,
    });
  }


  var teams = teamsSetOne.data;
  if (pageNum < 21) {
    const teamsSetTwo = await getTeamsSimple({pageNum: pageNum + 1}) ;

    if (teamsSetTwo.status !== 200) {
      throw new Response(null, {
        status: 500,
      });
    }

    if (teamsSetTwo.data.length === 0) {
      throw new Response(null, {
        status: 404,
      });
    }
    teams = teamsSetOne.data.concat(teamsSetTwo.data);
  }

  return { pageNum, teams: teams };
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

function TeamPageNumberToRange(pageNum: number): string {
  if (pageNum === 0) return "1-999";
  
  if (pageNum % 2 === 0) {
    let start = (pageNum) * 500;
    return `${start}s`;
  }
  
  let start = pageNum * 500;
  let end = start + 1000;

  return `${start}-${end}`
}


export default function TeamsPage() {
  const { pageNum, teams } = useLoaderData<typeof loader>();
  const navigate = useNavigate();

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <div className="basis-full lg:basis-1/6">
        <div className="lg:sticky top-14 pt-8">
          <Select
            value={String(pageNum)}
            onValueChange={(value) => {
              void navigate(`/teams/${value}`);
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder={TeamPageNumberToRange(pageNum)} />
            </SelectTrigger>
            <SelectContent>
              {pageNum % 2 === 1 && (
                <SelectItem key={pageNum} value={String(pageNum)}>
                  {TeamPageNumberToRange(pageNum)}
                </SelectItem>
              )}

              {Array.from({ length: Math.ceil(22 / 2) }, (_, i) => i * 2).map(page => (
                <SelectItem key={page} value={String(page)}>
                  {TeamPageNumberToRange(page)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="basis-full lg:py-8 lg:basis-5/6 overflow-x-auto">
        {<h1 className="mb-3 text-3xl font-medium">
          {} <em>FIRST</em> Robotics Teams {TeamPageNumberToRange(pageNum)}{' '}
          <small className="text-xl text-slate-500">
            {teams.length} Teams
          </small>
        </h1>}
        <TeamListTable teams={teams}/>
      </div>
    </div>
  );
}
