import type { LoaderFunctionArgs } from 'react-router';

export async function loader({ request }: LoaderFunctionArgs) {
  const response = await fetch(
    'https://www.thebluealliance.com/swagger/api_v3.json',
  );
  const json = await response.json();

  return new Response(JSON.stringify(json), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600',
    },
  });
}
