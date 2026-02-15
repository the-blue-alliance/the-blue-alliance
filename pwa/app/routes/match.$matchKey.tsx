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

    const { event, match } = loaderData;
    const playoffType = event.playoff_type ?? PlayoffType.CUSTOM;
    const title = matchTitleShort(match, playoffType);

    const videos = match.videos
      .filter((v) => v.type === 'youtube')
      .map((v) => ({
        '@type': 'VideoObject' as const,
        name: `${title} - ${event.name} ${event.year}`,
        url: `https://www.youtube.com/watch?v=${v.key}`,
        thumbnailUrl: `https://img.youtube.com/vi/${v.key}/hqdefault.jpg`,
      }));

    const jsonLd = {
      '@context': 'https://schema.org',
      '@type': 'SportsEvent',
      name: `${title} - ${event.name} ${event.year}`,
      description: `${title} at the ${event.year} ${event.name} FIRST Robotics Competition`,
      url: `https://www.thebluealliance.com/match/${match.key}`,
      ...(match.actual_time && {
        startDate: new Date(match.actual_time * 1000).toISOString(),
      }),
      location: {
        '@type': 'Place',
        name: event.location_name ?? event.name,
        address: {
          '@type': 'PostalAddress',
          addressLocality: event.city,
          addressRegion: event.state_prov,
          addressCountry: event.country,
        },
      },
      ...(videos.length > 0 && {
        subjectOf: videos.length === 1 ? videos[0] : videos,
      }),
      competitor: [
        {
          '@type': 'SportsTeam',
          name: 'Red Alliance',
          member: match.alliances.red.team_keys.map((key) => ({
            '@type': 'SportsTeam',
            name: `Team ${key.substring(3)}`,
            url: `https://www.thebluealliance.com/team/${key.substring(3)}`,
          })),
        },
        {
          '@type': 'SportsTeam',
          name: 'Blue Alliance',
          member: match.alliances.blue.team_keys.map((key) => ({
            '@type': 'SportsTeam',
            name: `Team ${key.substring(3)}`,
            url: `https://www.thebluealliance.com/team/${key.substring(3)}`,
          })),
        },
      ],
    };

    return {
      meta: [
        {
          title: `${title} - ${event.name} (${event.year}) - The Blue Alliance`,
        },
        {
          name: 'description',
          content: `${title} at the ${event.year} ${event.name} FIRST Robotics Competition in ${event.city}, ${event.state_prov}, ${event.country}`,
        },
      ],
      scripts: [
        {
          type: 'application/ld+json',
          children: JSON.stringify(jsonLd),
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
