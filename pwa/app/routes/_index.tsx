import type { MetaFunction } from '@remix-run/node';
import { json, useLoaderData } from '@remix-run/react';

import { getStatus } from '~/api/v3';

export async function loader() {
  return json({
    status: await getStatus({}),
  });
}

export const meta: MetaFunction = () => {
  return [
    { title: 'The Blue Alliance' },
    {
      name: 'description',
      content:
        'Team information and match videos and results from the FIRST Robotics Competition',
    },
  ];
};

export default function Index() {
  const { status } = useLoaderData<typeof loader>();

  return (
    <div className="p-4 font-sans">
      <h1 className="text-3xl">The Blue Alliance</h1>
      <p>
        The Blue Alliance is the best way to scout, watch, and relive the{' '}
        <i>FIRST</i> Robotics Competition.
      </p>
      <p>Current Season: {status.current_season}</p>
    </div>
  );
}
