import { useQuery } from '@tanstack/react-query';
import { Link, useLoaderData } from 'react-router';

import {
  getEvent,
  getEventAlliances,
  getEventMatches,
} from '~/api/tba/read';
import EliminationBracket from '~/components/tba/eliminationBracket';

export async function loader() {
  const eventKey = '2025gal';
  
  const [event, matches, alliances] = await Promise.all([
    getEvent({ path: { event_key: eventKey } }),
    getEventMatches({ path: { event_key: eventKey } }),
    getEventAlliances({ path: { event_key: eventKey } }),
  ]);

  if (event.data == undefined) {
    throw new Response(null, {
      status: 404,
    });
  }

  if (matches.data == undefined || alliances.data == undefined) {
    throw new Response(null, {
      status: 500,
    });
  }

  return {
    event: event.data,
    matches: matches.data,
    alliances: alliances.data,
  };
}

export default function TestBracketPage() {
  const { event, alliances, matches } = useLoaderData<typeof loader>();

  const elims = matches.filter((m) => m.comp_level !== 'qm');

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-4">
          <Link to={`/event/${event.key}`} className="text-blue-600 hover:underline">
            ← Back to {event.name}
          </Link>
        </div>
        
        <h1 className="text-3xl font-bold mb-6">
          {event.name} {event.year} - Elimination Bracket Test
        </h1>
        
        <div className="bg-white rounded-lg shadow p-6">
          <EliminationBracket
            alliances={alliances}
            matches={elims}
            year={event.year}
          />
        </div>
      </div>
    </div>
  );
}

export function meta() {
  return [
    { title: `Bracket Test - The Blue Alliance` },
    {
      name: 'description',
      content: `Test page for elimination bracket debugging.`,
    },
  ];
}