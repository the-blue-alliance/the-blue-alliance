import { json, LoaderFunctionArgs } from '@remix-run/node';
import { Link, useLoaderData } from '@remix-run/react';
import { getEvent, getEventAlliances, getEventMatches } from '~/api/v3';
import AllianceSelectionTable from '~/components/tba/allianceSelectionTable';
import InlineIcon from '~/components/tba/inlineIcon';
import { Badge } from '~/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { parseDateString } from '~/lib/utils';
import BiCalendar from '~icons/bi/calendar';
import BiGraphUp from '~icons/bi/graph-up';
import BiInfoCircleFill from '~icons/bi/info-circle-fill';
import BiLink from '~icons/bi/link';
import BiListOl from '~icons/bi/list-ol';
import BiPinMapFill from '~icons/bi/pin-map-fill';
import BiTrophy from '~icons/bi/trophy';
import MdiFolderMediaOutline from '~icons/mdi/folder-media-outline';
import MdiGraphBoxOutline from '~icons/mdi/graph-box-outline';
import MdiRobot from '~icons/mdi/robot';
import MdiTournament from '~icons/mdi/tournament';

export async function loader({ params }: LoaderFunctionArgs) {
  if (params.eventKey === undefined) {
    throw new Error('Missing eventKey');
  }

  const event = await getEvent({ eventKey: params.eventKey });
  const matches = await getEventMatches({ eventKey: params.eventKey });
  const alliances = await getEventAlliances({ eventKey: params.eventKey });

  return json({ event, matches, alliances });
}

export default function EventPage() {
  const { event, alliances, matches } = useLoaderData<typeof loader>();

  const startDate = parseDateString(event.start_date);
  const endDate = parseDateString(event.end_date);
  const startDateStr = startDate.toLocaleDateString('default', {
    month: 'long',
    day: 'numeric',
  });
  const endDateStr = endDate.toLocaleDateString('default', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <>
      <div className="mb-2.5 flex flex-col">
        <h1 className="mb-2.5 mt-5 text-4xl">
          {event.name} {event.year}
        </h1>

        <InlineIcon>
          <BiCalendar />
          {startDateStr} to {endDateStr}
          {event.week && (
            <Badge className="mx-2 h-[1.5em] align-text-top">
              Week {event.week + 1}
            </Badge>
          )}
        </InlineIcon>

        <InlineIcon>
          <BiPinMapFill />

          {event.gmaps_url ? (
            <Link to={event.gmaps_url}>
              {event.city}, {event.state_prov}, {event.country}
            </Link>
          ) : (
            <>
              {event.city}, {event.state_prov}, {event.country}
            </>
          )}
        </InlineIcon>
        {event.website && (
          <InlineIcon>
            <BiLink />
            <Link to={event.website}>{event.website}</Link>
          </InlineIcon>
        )}

        {event.first_event_code && (
          <InlineIcon>
            <BiInfoCircleFill />
            Details on{' '}
            <Link
              to={`https://frc-events.firstinspires.org/${event.year}/${event.first_event_code}`}
            >
              FRC Events
            </Link>
          </InlineIcon>
        )}

        <InlineIcon>
          <BiGraphUp />
          <Link to={`https://www.statbotics.io/event/${event.key}`}>
            Statbotics
          </Link>
        </InlineIcon>
      </div>

      <Tabs defaultValue="results" className="">
        <TabsList
          className="flex h-auto flex-wrap items-center justify-evenly [&>*]:basis-1/2
            lg:[&>*]:basis-1"
        >
          <TabsTrigger value="results">
            <InlineIcon>
              <MdiTournament />
              Results
            </InlineIcon>
          </TabsTrigger>
          <TabsTrigger value="rankings">
            <InlineIcon>
              <BiListOl />
              Rankings
            </InlineIcon>
          </TabsTrigger>
          <TabsTrigger value="awards">
            <InlineIcon>
              <BiTrophy />
              Awards
            </InlineIcon>
          </TabsTrigger>
          <TabsTrigger value="teams">
            <InlineIcon>
              <MdiRobot />
              Teams
            </InlineIcon>
          </TabsTrigger>
          <TabsTrigger value="insights">
            <InlineIcon>
              <MdiGraphBoxOutline />
              Insights
            </InlineIcon>
          </TabsTrigger>
          <TabsTrigger value="media">
            <InlineIcon>
              <MdiFolderMediaOutline />
              Media
            </InlineIcon>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="results">
          <div className="flex">
            <div className="w-1/2 shrink-0">{matches.length} matches</div>

            <AllianceSelectionTable alliances={alliances} />
          </div>
        </TabsContent>

        <TabsContent value="rankings">rankings</TabsContent>

        <TabsContent value="awards">awards</TabsContent>

        <TabsContent value="teams">teams</TabsContent>

        <TabsContent value="insights">insights</TabsContent>

        <TabsContent value="media">media</TabsContent>
      </Tabs>
    </>
  );
}
