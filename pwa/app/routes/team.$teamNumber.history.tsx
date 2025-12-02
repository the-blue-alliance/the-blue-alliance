import { useLoaderData, useNavigate } from 'react-router';
import { Fragment } from 'react/jsx-runtime';

import {
  getTeam,
  getTeamHistory,
  getTeamSocialMedia,
  getTeamYearsParticipated,
} from '~/api/tba/read';
import { AwardBanner } from '~/components/tba/banner';
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
import { BLUE_BANNER_AWARDS } from '~/lib/api/AwardType';
import { SEASON_EVENT_TYPES } from '~/lib/api/EventType';
import { sortAwardsByEventDate } from '~/lib/awardUtils';
import { sortEventsComparator } from '~/lib/eventUtils';
import { joinComponents } from '~/lib/utils';

import { Route } from '.react-router/types/app/routes/+types/team.$teamNumber.history';

async function loadData(params: Route.LoaderArgs['params']) {
  const teamKey = `frc${params.teamNumber}`;

  const [team, history, yearsParticipated, socials] = await Promise.all([
    getTeam({ path: { team_key: teamKey } }),
    getTeamHistory({ path: { team_key: teamKey } }),
    getTeamYearsParticipated({ path: { team_key: teamKey } }),
    getTeamSocialMedia({ path: { team_key: teamKey } }),
  ]);

  if (team.data === undefined) {
    throw new Response(null, { status: 404 });
  }

  if (
    history.data === undefined ||
    yearsParticipated.data === undefined ||
    socials.data === undefined
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

export async function loader({ params }: Route.LoaderArgs) {
  return await loadData(params);
}

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return await loadData(params);
}

export function meta({ data }: Route.MetaArgs) {
  if (!data) {
    return [
      {
        title: `Team History - The Blue Alliance`,
      },
      {
        name: 'description',
        content: `Team history for the FIRST Robotics Competition.`,
      },
    ];
  }

  return [
    {
      title: `${data.team.nickname} - Team ${data.team.team_number} (History) - The Blue Alliance`,
    },
    {
      name: 'description',
      content:
        `From ${data.team.city}, ${data.team.state_prov} ${data.team.postal_code}, ${data.team.country}.` +
        ' Team information, match results, and match videos from the FIRST Robotics Competition.',
    },
  ];
}

export default function TeamPage(): React.JSX.Element {
  const navigate = useNavigate();
  const { team, history, yearsParticipated, socials } =
    useLoaderData<typeof loader>();

  yearsParticipated.sort((a, b) => b - a);
  history.events.sort(sortEventsComparator).reverse();
  const awardsSortedByEventDate = sortAwardsByEventDate(
    history.awards,
    history.events,
  ).toReversed();

  const bannerAwards = awardsSortedByEventDate
    .filter((a) => BLUE_BANNER_AWARDS.has(a.award_type))
    .filter((a) =>
      SEASON_EVENT_TYPES.has(
        history.events.find((e) => e.key === a.event_key)?.event_type ?? -1,
      ),
    );

  return (
    <div className="flex flex-wrap sm:flex-nowrap">
      <div className="top-0 mr-4 pt-5 sm:sticky">
        <Select
          onValueChange={(value) => {
            void navigate(`/team/${team.team_number}/${value}`);
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
        <div
          className="flex flex-wrap justify-center sm:flex-nowrap
            sm:justify-between"
        >
          <div className="flex flex-col justify-between">
            <TeamPageTeamInfo
              maybeAvatar={undefined}
              socials={socials}
              team={team}
            />
          </div>
        </div>

        <Separator className="my-4" />

        <div className="flex flex-row gap-4">
          <Table className="w-auto">
            <TableHeader>
              <TableRow>
                <TableHead className="w-[6ch]">Year</TableHead>
                <TableHead className="w-[40ch]">Event</TableHead>
                <TableHead className="w-[40ch]">Awards</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {history.events.map((e, i) => (
                <Fragment key={e.key}>
                  {(i == 0 || history.events[i - 1].year !== e.year) && (
                    <TableRow>
                      <TableCell
                        rowSpan={
                          history.events.filter((e2) => e2.year === e.year)
                            .length + 1
                        }
                      >
                        <TeamLink teamOrKey={team} year={e.year}>
                          {e.year}
                        </TeamLink>
                      </TableCell>
                    </TableRow>
                  )}
                  <TableRow>
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
                </Fragment>
              ))}
            </TableBody>
          </Table>
          <div>
            {bannerAwards.length > 0 && (
              <div className="flex w-96 flex-row flex-wrap justify-center gap-2">
                {bannerAwards.map((a) => (
                  <AwardBanner
                    key={`${a.award_type}-${a.event_key}`}
                    award={a}
                    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                    event={history.events.find((e) => e.key === a.event_key)!}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
