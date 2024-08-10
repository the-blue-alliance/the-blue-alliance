import { json, LoaderFunctionArgs } from '@remix-run/node';
import {
  type ClientLoaderFunctionArgs,
  Link,
  Params,
  useLoaderData,
} from '@remix-run/react';
import { useMemo } from 'react';
import {
  Award,
  getEvent,
  getEventAlliances,
  getEventAwards,
  getEventMatches,
  getEventRankings,
} from '~/api/v3';
import AllianceSelectionTable from '~/components/tba/allianceSelectionTable';
import AwardRecipientLink from '~/components/tba/awardRecipientLink';
import InlineIcon from '~/components/tba/inlineIcon';
import MatchResultsTable from '~/components/tba/matchResultsTable';
import RankingsTable from '~/components/tba/rankingsTable';
import { Badge } from '~/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import {
  parseDateString,
  sortAwardsComparator,
  sortTeamKeysComparator,
} from '~/lib/utils';
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

async function loadData(params: Params) {
  if (params.eventKey === undefined) {
    throw new Error('Missing eventKey');
  }

  const [event, matches, alliances, rankings, awards] = await Promise.all([
    getEvent({ eventKey: params.eventKey }),
    getEventMatches({ eventKey: params.eventKey }),
    getEventAlliances({ eventKey: params.eventKey }),
    getEventRankings({ eventKey: params.eventKey }),
    getEventAwards({ eventKey: params.eventKey }),
  ]);

  return { event, matches, alliances, rankings, awards };
}

export async function loader({ params }: LoaderFunctionArgs) {
  return json(await loadData(params));
}

export async function clientLoader({ params }: ClientLoaderFunctionArgs) {
  return await loadData(params);
}

export default function EventPage() {
  const { event, alliances, matches, rankings, awards } =
    useLoaderData<typeof loader>();

  const startDate = event.start_date ? parseDateString(event.start_date) : null;
  const endDate = event.end_date ? parseDateString(event.end_date) : null;
  const startDateStr = startDate
    ? startDate.toLocaleDateString('default', {
        month: 'long',
        day: 'numeric',
      })
    : '';
  const endDateStr = endDate
    ? endDate.toLocaleDateString('default', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      })
    : '';

  const quals = useMemo(
    () => matches.filter((m) => m.comp_level === 'qm'),
    [matches],
  );

  return (
    <>
      <div className="mb-2.5 flex flex-col">
        <h1 className="mb-2.5 mt-5 text-4xl">
          {event.name} {event.year}
        </h1>

        <InlineIcon>
          <BiCalendar />
          {startDateStr} to {endDateStr}
          {event.week !== undefined && event.week !== null && (
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
          <div className="flex flex-wrap gap-4 lg:flex-nowrap">
            <div className="basis-full lg:basis-1/2">
              <MatchResultsTable
                matches={quals}
                title="Qualification Matches"
              />
            </div>

            <div className="basis-full lg:basis-1/2">
              <AllianceSelectionTable alliances={alliances ?? []} />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="rankings">
          <RankingsTable
            rankings={rankings}
            winners={
              alliances?.find((a) => a.status?.status === 'won')?.picks ?? []
            }
          />
        </TabsContent>

        <TabsContent value="awards">
          <AwardsTab awards={awards} />
        </TabsContent>

        <TabsContent value="teams">teams</TabsContent>

        <TabsContent value="insights">insights</TabsContent>

        <TabsContent value="media">media</TabsContent>
      </Tabs>
    </>
  );
}

function AwardsTab({ awards }: { awards: Award[] }) {
  awards.sort(sortAwardsComparator);
  return (
    <div className="flex flex-wrap-reverse">
      <div className="mt-1 flow-root w-full">
        <dl className="divide-y divide-gray-100 text-sm">
          {awards.map((award) => (
            <div
              key={award.name}
              className="grid grid-cols-1 gap-1 py-2 sm:grid-cols-3 sm:gap-4 sm:px-10"
            >
              <dt className="font-medium text-gray-900 sm:col-span-2">
                {award.name}
              </dt>
              <dd className="text-gray-700 sm:text-right">
                {award.recipient_list
                  .sort((a, b) =>
                    sortTeamKeysComparator(
                      a.team_key ?? '0',
                      b.team_key ?? '0',
                    ),
                  )
                  .map((r, i) => [
                    i > 0 && (r.awardee ? <br /> : ', '),
                    <AwardRecipientLink
                      recipient={r}
                      key={`${award.award_type}-${r.awardee}-${r.team_key}`}
                    />,
                  ])}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}
