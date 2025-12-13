import { createFileRoute, notFound } from '@tanstack/react-router';

import { getEvent, getMatch } from '~/api/tba/read';
import { EventLink } from '~/components/tba/links';
import MatchDetails from '~/components/tba/match/matchDetails';
import { PlayoffType } from '~/lib/api/PlayoffType';
import { isValidMatchKey, matchTitleShort } from '~/lib/matchUtils';
import { publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/match/$matchKey')({
  loader: async ({ params }) => {
    if (!isValidMatchKey(params.matchKey)) {
      throw notFound();
    }

    const eventKey = params.matchKey.split('_')[0];

    const [event, match] = await Promise.all([
      getEvent({ path: { event_key: eventKey } }),
      getMatch({ path: { match_key: params.matchKey } }),
    ]);

    if (event.data === undefined || match.data === undefined) {
      throw notFound();
    }

    return {
      event: event.data,
      match: match.data,
    };
  },
  headers: publicCacheControlHeaders(),
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [
          { title: 'Match Information - The Blue Alliance' },
          {
            name: 'description',
            content: 'Match information for the FIRST Robotics Competition.',
          },
        ],
      };
    }

    return {
      meta: [
        {
          title: `${matchTitleShort(loaderData.match, loaderData.event.playoff_type ?? PlayoffType.CUSTOM)} - ${loaderData.event.name} (${loaderData.event.year}) - The Blue Alliance`,
        },
        {
          name: 'description',
          content: `${matchTitleShort(loaderData.match, loaderData.event.playoff_type ?? PlayoffType.CUSTOM)} at the ${loaderData.event.year} ${loaderData.event.name} FIRST Robotics Competition in ${loaderData.event.city}, ${loaderData.event.state_prov}, ${loaderData.event.country}`,
        },
      ],
    };
  },
  component: MatchPage,
});

function MatchPage() {
  const { event, match } = Route.useLoaderData();

  return (
    <div>
      <h1 className="mt-8 mb-4 text-4xl">
        {matchTitleShort(match, event.playoff_type ?? PlayoffType.CUSTOM)}{' '}
        <small className="text-xl">
          <EventLink eventOrKey={event}>
            {event.name} {event.year}
          </EventLink>
        </small>
      </h1>
      <MatchDetails match={match} event={event} />
    </div>
  );
}
