import type { MetaFunction } from '@remix-run/node';
import { json, useLoaderData } from '@remix-run/react';
import { Theme, useTheme } from 'remix-themes';

import { getStatus } from '~/api/v3';
import { Button } from '~/components/ui/button';

export async function loader() {
  const status = await getStatus({});

  if (status.status !== 200) {
    throw new Response(null, {
      status: 500,
    });
  }

  return json({
    status: status.data,
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
  const [, setTheme] = useTheme();

  // Commit hash is string-replaced, so we need to ignore eslint and typescript errors.
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-expect-error
  const commitHash = __COMMIT_HASH__ as string;

  return (
    <div className="p-4 font-sans">
      <h1 className="text-3xl">The Blue Alliance</h1>
      <p>
        The Blue Alliance is the best way to scout, watch, and relive the{' '}
        <i>FIRST</i> Robotics Competition.
      </p>
      <p>Current Season: {status.current_season}</p>
      <a
        href={`https://github.com/the-blue-alliance/the-blue-alliance/commit/${commitHash}`}
        target="_blank"
        rel="noreferrer"
      >
        Commit: {commitHash}
      </a>
      <Button onClick={() => setTheme(Theme.LIGHT)}>Light</Button>
      <Button onClick={() => setTheme(Theme.DARK)}>Dark</Button>
    </div>
  );
}
