import { useLoaderData } from 'react-router';

import { getEvent, getMatch } from '~/api/tba/read';
import { EventLink } from '~/components/tba/links';
import { isValidMatchKey, matchTitleShort } from '~/lib/matchUtils';

import { Route } from '.react-router/types/app/routes/+types/match.$matchKey';

async function loadData(params: Route.LoaderArgs['params']) {
  if (!isValidMatchKey(params.matchKey)) {
    throw new Response(null, {
      status: 404,
    });
  }

  const eventKey = params.matchKey.split('_')[0];

  const [event, match] = await Promise.all([
    getEvent({ path: { event_key: eventKey } }),
    getMatch({ path: { match_key: params.matchKey } }),
  ]);

  if (event.data === undefined || match.data === undefined) {
    throw new Response(null, {
      status: 404,
    });
  }

  return {
    event: event.data,
    match: match.data,
  };
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
      title: `${matchTitleShort(data.match, data.event)} - ${data.event.name} (${data.event.year}) - The Blue Alliance`,
    },
    {
      name: 'description',
      content: `${matchTitleShort(data.match, data.event)} at the ${data.event.year} ${data.event.name} FIRST Robotics Competition in ${data.event.city}, ${data.event.state_prov}, ${data.event.country}`,
    },
  ];
}

export default function MatchPage() {
  const { event, match } = useLoaderData<typeof loader>();
  return (
    <div>
      <h1 className="mt-5 text-4xl">
        {matchTitleShort(match, event)}{' '}
        <small className="text-xl">
          <EventLink eventOrKey={event}>
            {event.name} {event.year}
          </EventLink>
        </small>
      </h1>
    </div>
  );
}
