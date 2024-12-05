import { LoaderFunctionArgs } from '@remix-run/node';
import {
  type ClientLoaderFunctionArgs,
  MetaFunction,
  Params,
  useLoaderData,
} from '@remix-run/react';

import { getEvent, getMatch } from '~/api/v3';
import { EventLink } from '~/components/tba/links';
import { isValidMatchKey, matchTitleShort } from '~/lib/matchUtils';

async function loadData(params: Params) {
  if (params.matchKey === undefined) {
    throw new Error('Missing matchKey');
  }

  if (!isValidMatchKey(params.matchKey)) {
    throw new Response(null, {
      status: 404,
    });
  }

  const eventKey = params.matchKey.split('_')[0];

  const [event, match] = await Promise.all([
    getEvent({ eventKey }),
    getMatch({ matchKey: params.matchKey }),
  ]);

  if (event.status == 404 || match.status == 404) {
    throw new Response(null, {
      status: 404,
    });
  }

  if (event.status !== 200 || match.status !== 200) {
    throw new Response(null, {
      status: 500,
    });
  }

  return {
    event: event.data,
    match: match.data,
  };
}

export async function loader({ params }: LoaderFunctionArgs) {
  return await loadData(params);
}

export async function clientLoader({ params }: ClientLoaderFunctionArgs) {
  return await loadData(params);
}

export const meta: MetaFunction<typeof loader> = ({ data }) => {
  const match = data?.match;
  const event = data?.event;
  if (!match || !event) {
    return;
  }
  return [
    {
      title: `${matchTitleShort(match, event)} - ${event.name} (${event.year}) - The Blue Alliance`,
    },
    {
      name: 'description',
      content: `${matchTitleShort(match, event)} at the ${event.year} ${event.name} FIRST Robotics Competition in ${event.city}, ${event.state_prov}, ${event.country}`,
    },
  ];
};

export default function EventPage() {
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
