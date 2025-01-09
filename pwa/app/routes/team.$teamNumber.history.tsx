import { LoaderFunctionArgs } from 'react-router';
import {
  ClientLoaderFunctionArgs,
  MetaFunction,
  Params,
  useLoaderData,
  useNavigate,
} from 'react-router';

import {
  getTeam,
  getTeamHistory,
  getTeamSocialMedia,
  getTeamYearsParticipated,
} from '~/api/v3';
import { EventLink, TeamLink } from '~/components/tba/links';
import TeamPageTeamInfo from '~/components/tba/teamPageTeamInfo';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import { Separator } from '~/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { joinComponents } from '~/lib/utils';

async function loadData(params: Params) {
  if (params.teamNumber === undefined) {
    throw new Error('missing team number');
  }

  const teamKey = `frc${params.teamNumber}`;

  const [team, history, yearsParticipated, socials] = await Promise.all([
    getTeam({ teamKey }),
    getTeamHistory({ teamKey }),
    getTeamYearsParticipated({ teamKey }),
    getTeamSocialMedia({ teamKey }),
  ]);

  if (team.status === 404) {
    throw new Response(null, { status: 404 });
  }

  if (
    team.status !== 200 ||
    history.status !== 200 ||
    yearsParticipated.status !== 200 ||
    socials.status !== 200
  ) {
    throw new Response(null, { status: 500 });
  }

  history.data.events
    .sort(
      (a, b) =>
        a.year - b.year ||
        (a.week ?? 100) - (b.week ?? 100) ||
        Date.parse(a.start_date) - Date.parse(b.start_date),
    )
    .reverse();

  return {
    team: team.data,
    history: history.data,
    yearsParticipated: yearsParticipated.data,
    socials: socials.data,
  };
}

export async function loader({ params }: LoaderFunctionArgs) {
  return await loadData(params);
}

export async function clientLoader({ params }: ClientLoaderFunctionArgs) {
  return await loadData(params);
}

export const meta: MetaFunction<typeof loader> = ({ data }) => {
  return [
    {
      title: `${data?.team.nickname} - Team ${data?.team.team_number} (History) - The Blue Alliance`,
    },
    {
      name: 'description',
      content:
        `From ${data?.team.city}, ${data?.team.state_prov} ${data?.team.postal_code}, ${data?.team.country}.` +
        ' Team information, match results, and match videos from the FIRST Robotics Competition.',
    },
  ];
};

export default function TeamPage(): React.JSX.Element {
  const navigate = useNavigate();
  const { team, history, yearsParticipated, socials } =
    useLoaderData<typeof loader>();

  yearsParticipated.sort((a, b) => b - a);

  return (
    <div className="flex flex-wrap sm:flex-nowrap">
      <div className="top-0 mr-4 pt-5 sm:sticky">
        <Select
          onValueChange={(value) => {
            navigate(`/team/${team.team_number}/${value}`);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder={'History'} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="History">History</SelectItem>
            {yearsParticipated.map((y) => (
              <SelectItem key={y} value={`${y}`}>
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="mt-5 w-full">
        <div className="flex flex-wrap justify-center sm:flex-nowrap sm:justify-between">
          <div className="flex flex-col justify-between">
            <TeamPageTeamInfo
              maybeAvatar={undefined}
              socials={socials}
              team={team}
            />
          </div>
        </div>

        <Separator className="my-4" />

        <Table className="w-auto">
          <TableHeader>
            <TableRow>
              <TableHead className="w-[6ch]">Year</TableHead>
              <TableHead className="w-[40ch]">Event</TableHead>
              <TableHead className="w-[40ch]">Awards</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {history.events.map((e) => (
              <TableRow key={e.key}>
                <TableCell>
                  <TeamLink teamOrKey={team} year={e.year}>
                    {e.year}
                  </TeamLink>
                </TableCell>
                <TableCell>
                  <EventLink eventOrKey={e}>{e.name}</EventLink>
                </TableCell>
                <TableCell>
                  {joinComponents(
                    history.awards
                      .filter((a) => a.event_key === e.key)
                      .map((a) => {
                        const teamRecipients = a.recipient_list
                          .filter((r) => r.awardee !== null)
                          .filter((r) => r.awardee !== '')
                          .filter((r) => r.team_key === team.key)
                          .map((r) => r.awardee);

                        return (
                          <span key={`${a.event_key}_${a.award_type}`}>
                            {a.name}
                            {teamRecipients.length > 0 &&
                              ` (${teamRecipients.join(', ')})`}
                          </span>
                        );
                      }),
                    <br />,
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
