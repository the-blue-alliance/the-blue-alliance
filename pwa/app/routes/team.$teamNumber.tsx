import { LoaderFunctionArgs } from '@remix-run/node';
import {
  ClientLoaderFunctionArgs,
  Link,
  MetaFunction,
  Params,
  json,
  useLoaderData,
} from '@remix-run/react';
import { useMemo } from 'react';

import BiCalendar from '~icons/bi/calendar';
import BiGraphUp from '~icons/bi/graph-up';
import BiInfoCircleFill from '~icons/bi/info-circle-fill';
import BiLink from '~icons/bi/link';
import BiPinMapFill from '~icons/bi/pin-map-fill';

import { getTeam, getTeamMediaByYear } from '~/api/v3';
import InlineIcon from '~/components/tba/inlineIcon';
import TeamAvatar from '~/components/tba/teamAvatar';
import TeamRobotPicsCarousel from '~/components/tba/teamRobotPicsCarousel';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '~/components/ui/accordion';
import { Badge } from '~/components/ui/badge';
import {
  attemptToParseSchoolNameFromOldTeamName,
  attemptToParseSponsors,
} from '~/lib/teamUtils';

async function loadData(params: Params) {
  if (params.teamNumber === undefined) {
    throw new Error('missing team number');
  }

  const teamKey = `frc${params.teamNumber}`;
  // todo: add year support
  const year = 2024;

  const [team, media] = await Promise.all([
    getTeam({ teamKey }),
    getTeamMediaByYear({ teamKey, year }),
  ]);

  if (team.status === 404) {
    throw new Response(null, { status: 404 });
  }

  if (team.status !== 200 || media.status !== 200) {
    throw new Response(null, { status: 500 });
  }

  return { team: team.data, media: media.data };
}

export async function loader({ params }: LoaderFunctionArgs) {
  return json(await loadData(params));
}

export async function clientLoader({ params }: ClientLoaderFunctionArgs) {
  return await loadData(params);
}

export const meta: MetaFunction<typeof loader> = ({ data }) => {
  return [
    {
      title: `${data?.team.nickname} - Team ${data?.team.team_number} - The Blue Alliance`,
    },
    {
      name: 'description',
      content:
        `From ${data?.team.city}, ${data?.team.state_prov} ${data?.team.postal_code}, ${data?.team.country}.` +
        ' Team information, match results, and match videos from the FIRST Robotics Competition.',
    },
  ];
};

export default function TeamPage(): JSX.Element {
  const { team, media } = useLoaderData<typeof loader>();

  const robotPics = useMemo(
    () =>
      media
        .filter((m) => m.type === 'imgur')
        .sort((a, b) => {
          if (a.preferred) {
            return -1;
          }
          if (b.preferred) {
            return 1;
          }

          return 0;
        }),
    [media],
  );

  const maybeAvatar = useMemo(
    () => media.find((m) => m.type === 'avatar'),
    [media],
  );

  const sponsors = attemptToParseSponsors(team.name);
  const schoolName =
    team.school_name ?? attemptToParseSchoolNameFromOldTeamName(team.name);

  return (
    <div className="flex flex-wrap justify-center">
      <div className="basis-1/2">
        <h1 className="mb-2.5 mt-5 text-4xl">
          {maybeAvatar && <TeamAvatar media={maybeAvatar} />}
          Team {team.team_number} - {team.nickname}
        </h1>

        <InlineIcon>
          <BiPinMapFill />
          {team.city}, {team.state_prov}, {team.country}
        </InlineIcon>

        {sponsors.length > 0 ? (
          <Accordion type="single" collapsible>
            <AccordionItem value="item-1" className="border-0">
              <AccordionTrigger className="p-0 text-left font-normal">
                <InlineIcon displayStyle={'flexless'}>
                  <BiInfoCircleFill />
                  {schoolName}
                  {sponsors.length > 0 && ` with ${sponsors.length} sponsor`}
                  {sponsors.length > 1 && 's'}
                </InlineIcon>
              </AccordionTrigger>
              <AccordionContent className="pb-0">
                {sponsors.map((sponsor, i) => (
                  <Badge
                    className="m-px font-normal"
                    key={i}
                    variant={'secondary'}
                  >
                    {sponsor}
                  </Badge>
                ))}
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        ) : (
          <InlineIcon displayStyle={'flexless'}>
            <BiInfoCircleFill />
            {schoolName}
          </InlineIcon>
        )}

        <InlineIcon>
          <BiCalendar />
          Rookie Year: {team.rookie_year}
        </InlineIcon>

        <InlineIcon>
          <BiLink />
          Details on{' '}
          <Link
            to={`https://frc-events.firstinspires.org/team/${team.team_number}`}
          >
            FRC Events
          </Link>
        </InlineIcon>

        <InlineIcon>
          <BiGraphUp />
          <Link to={`https://www.statbotics.io/team/${team.team_number}`}>
            Statbotics
          </Link>
        </InlineIcon>
      </div>
      <div className="">
        <TeamRobotPicsCarousel media={robotPics} />
      </div>
    </div>
  );
}
