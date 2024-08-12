import { LoaderFunctionArgs } from '@remix-run/node';
import {
  ClientLoaderFunctionArgs,
  json,
  Params,
  useLoaderData,
} from '@remix-run/react';
import { getTeam } from '~/api/v3';

async function loadData(params: Params) {
  if (params.teamNumber === undefined) {
    throw new Error('missing team number');
  }

  const teamKey = `frc${params.teamNumber}`;

  const [team] = await Promise.all([getTeam({ teamKey })]);

  if (team.status === 404) {
    throw new Response(null, { status: 404 });
  }

  if (team.status !== 200) {
    throw new Response(null, { status: 500 });
  }

  return { team: team.data };
}

export async function loader({ params }: LoaderFunctionArgs) {
  return json(await loadData(params));
}

export async function clientLoader({ params }: ClientLoaderFunctionArgs) {
  return await loadData(params);
}

export default function TeamPage(): JSX.Element {
  const { team } = useLoaderData<typeof loader>();

  return (
    <div>
      <div className="text-3xl font-semibold">
        Team {team.team_number} - {team.nickname}
      </div>
    </div>
  );
}
