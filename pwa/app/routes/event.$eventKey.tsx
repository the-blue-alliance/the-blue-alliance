import { json, LoaderFunctionArgs } from '@remix-run/node';
import {
  type ClientLoaderFunctionArgs,
  Link,
  MetaFunction,
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
  getEventTeams,
  Team,
} from '~/api/v3';
import AllianceSelectionTable from '~/components/tba/allianceSelectionTable';
import AwardRecipientLink from '~/components/tba/awardRecipientLink';
import InlineIcon from '~/components/tba/inlineIcon';
import MatchResultsTableDoubleElim from '~/components/tba/matchResultsTables/doubleElim';
import MatchResultsTableQuals from '~/components/tba/matchResultsTables/quals';
import RankingsTable from '~/components/tba/rankingsTable';
import { Badge } from '~/components/ui/badge';
import { Card } from '~/components/ui/card';
import {
  Credenza,
  CredenzaBody,
  CredenzaClose,
  CredenzaContent,
  CredenzaDescription,
  CredenzaFooter,
  CredenzaHeader,
  CredenzaTitle,
  CredenzaTrigger,
} from '~/components/ui/credenza';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { sortAwardsComparator } from '~/lib/awardUtils';
import { getEventDateString } from '~/lib/eventUtils';
import { sortMatchComparator } from '~/lib/matchUtils';
import { sortTeamKeysComparator, sortTeamsComparator } from '~/lib/teamUtils';
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

  const [event, matches, alliances, rankings, awards, teams] =
    await Promise.all([
      getEvent({ eventKey: params.eventKey }),
      getEventMatches({ eventKey: params.eventKey }),
      getEventAlliances({ eventKey: params.eventKey }),
      getEventRankings({ eventKey: params.eventKey }),
      getEventAwards({ eventKey: params.eventKey }),
      getEventTeams({ eventKey: params.eventKey }),
    ]);

  if (event.status == 404) {
    throw new Response(null, {
      status: 404,
    });
  }

  if (
    event.status !== 200 ||
    matches.status !== 200 ||
    alliances.status !== 200 ||
    rankings.status !== 200 ||
    awards.status !== 200 ||
    teams.status !== 200
  ) {
    throw new Response(null, {
      status: 500,
    });
  }

  return {
    event: event.data,
    matches: matches.data,
    alliances: alliances.data,
    rankings: rankings.data,
    awards: awards.data,
    teams: teams.data,
  };
}

export async function loader({ params }: LoaderFunctionArgs) {
  return json(await loadData(params));
}

export async function clientLoader({ params }: ClientLoaderFunctionArgs) {
  return await loadData(params);
}

export const meta: MetaFunction<typeof loader> = ({ data }) => {
  return [
    { title: `${data?.event.name} (${data?.event.year}) - The Blue Alliance` },
    {
      name: 'description',
      content: `Videos and match results for the ${data?.event.year} ${data?.event.name} FIRST Robotics Competition.`,
    },
  ];
};

export default function EventPage() {
  const { event, alliances, matches, rankings, awards, teams } =
    useLoaderData<typeof loader>();

  const sortedMatches = useMemo(
    () => matches.sort(sortMatchComparator),
    [matches],
  );

  const quals = useMemo(
    () => sortedMatches.filter((m) => m.comp_level === 'qm'),
    [sortedMatches],
  );

  const elims = useMemo(
    () => sortedMatches.filter((m) => m.comp_level !== 'qm'),
    [sortedMatches],
  );

  const leftSideMatches =
    quals.length > 0 ? (
      <MatchResultsTableQuals matches={quals} />
    ) : (
      <MatchResultsTableDoubleElim matches={elims} />
    );

  const rightSideElims =
    quals.length > 0 ? <MatchResultsTableDoubleElim matches={elims} /> : <></>;

  return (
    <>
      <div className="mb-2.5 flex flex-col">
        <h1 className="mb-2.5 mt-5 text-4xl">
          {event.name} {event.year}
        </h1>

        <InlineIcon>
          <BiCalendar />
          {getEventDateString(event, 'long')}
          {event.week !== null && (
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
            <div className="basis-full lg:basis-1/2">{leftSideMatches}</div>

            <div className="basis-full lg:basis-1/2">
              <AllianceSelectionTable alliances={alliances ?? []} />
              {rightSideElims}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="rankings">
          <RankingsTable
            rankings={rankings}
            winners={
              alliances?.find((a) => a.status.status === 'won')?.picks ?? []
            }
          />
        </TabsContent>

        <TabsContent value="awards">
          <AwardsTab awards={awards} />
        </TabsContent>

        <TabsContent value="teams">
          <TeamsTab teams={teams} />
        </TabsContent>

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

function TeamsTab({ teams }: { teams: Team[] }) {
  teams.sort(sortTeamsComparator);

  // Lot todo here:
  // 1. add robot images
  // 2. create a TeamEvent component that shows schedule, etc, which is inside CredenzaBody
  // 3. add hover effects
  // 4. split out CredenzaTrigger, so the same UI (Body) can be triggered by different UI elements
  return (
    <div className="md:columns-2">
      {teams.map((t) => (
        <Credenza key={t.key}>
          <CredenzaTrigger asChild>
            <Card className="my-1 flex cursor-pointer items-center gap-4 rounded-lg bg-background p-4">
              <div className="grid flex-1 gap-1">
                <div className="font-medium">
                  {t.team_number} - {t.nickname}
                </div>
                <div className="text-sm text-muted-foreground">
                  {t.city}, {t.state_prov}, {t.country}
                </div>
              </div>
              <img
                src="https://placehold.co/400x400"
                alt=""
                className="size-20"
              />
            </Card>
          </CredenzaTrigger>
          <CredenzaContent>
            <CredenzaHeader>
              <CredenzaTitle>
                {t.team_number} - {t.nickname}
              </CredenzaTitle>
              <CredenzaDescription>
                {t.city}, {t.state_prov}, {t.country}
              </CredenzaDescription>
            </CredenzaHeader>
            <CredenzaBody>Full name: {t.name}</CredenzaBody>
            <CredenzaFooter>
              <CredenzaClose asChild>
                <button>Close</button>
              </CredenzaClose>
            </CredenzaFooter>
          </CredenzaContent>
        </Credenza>
      ))}
    </div>
  );
}
