import { useQuery, useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';
import { Fragment } from 'react/jsx-runtime';

import {
  getTeamHistoryOptions,
  getTeamOptions,
  getTeamSocialMediaOptions,
  getTeamYearsParticipatedOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { AwardBanner } from '~/components/tba/banner';
import { EventLink, TeamLink } from '~/components/tba/links';
import TeamPageTeamInfo from '~/components/tba/teamPageTeamInfo';
import { YearSelector } from '~/components/tba/yearSelector';
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
import {
  doThrowNotFound,
  joinComponents,
  publicCacheControlHeaders,
} from '~/lib/utils';

export const Route = createFileRoute('/team/$teamNumber/history')({
  loader: async ({ params, context: { queryClient } }) => {
    const teamKey = `frc${params.teamNumber}`;

    // spawn these now, we don't need to await them yet though
    const yearsParticipatedQuery = queryClient
      .ensureQueryData(
        getTeamYearsParticipatedOptions({ path: { team_key: teamKey } }),
      )
      .catch(() => []);
    const socialsQuery = queryClient
      .ensureQueryData(
        getTeamSocialMediaOptions({ path: { team_key: teamKey } }),
      )
      .catch(() => []);

    const [team] = await Promise.all([
      queryClient
        .ensureQueryData(getTeamOptions({ path: { team_key: teamKey } }))
        .catch(doThrowNotFound),
      queryClient
        .ensureQueryData(getTeamHistoryOptions({ path: { team_key: teamKey } }))
        .catch(doThrowNotFound),
      yearsParticipatedQuery,
      socialsQuery,
    ]);

    // team needs to be returned so we can access it in meta
    return { teamKey, team };
  },
  headers: publicCacheControlHeaders(),
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [
          { title: 'Team History - The Blue Alliance' },
          {
            name: 'description',
            content: 'Team history for the FIRST Robotics Competition.',
          },
        ],
      };
    }

    return {
      meta: [
        {
          title: `${loaderData.team.nickname} - Team ${loaderData.team.team_number} (History) - The Blue Alliance`,
        },
        {
          name: 'description',
          content:
            `From ${loaderData.team.city}, ${loaderData.team.state_prov} ${loaderData.team.postal_code}, ${loaderData.team.country}.` +
            ' Team information, match results, and match videos from the FIRST Robotics Competition.',
        },
      ],
    };
  },
  component: TeamHistoryPage,
});

function TeamHistoryPage(): React.JSX.Element {
  const { teamKey } = Route.useLoaderData();

  const { data: team } = useSuspenseQuery(
    getTeamOptions({ path: { team_key: teamKey } }),
  );
  const { data: history } = useSuspenseQuery(
    getTeamHistoryOptions({ path: { team_key: teamKey } }),
  );
  const yearsParticipatedQuery = useQuery(
    getTeamYearsParticipatedOptions({ path: { team_key: teamKey } }),
  );
  const socialsQuery = useQuery(
    getTeamSocialMediaOptions({ path: { team_key: teamKey } }),
  );

  // These arrays live in the query cache, so sort copies rather than in place.
  const yearsParticipated = (yearsParticipatedQuery.data ?? []).toSorted(
    (a, b) => b - a,
  );
  const socials = socialsQuery.data ?? [];
  const events = history.events.toSorted(sortEventsComparator).toReversed();
  const awardsSortedByEventDate = sortAwardsByEventDate(
    history.awards,
    events,
  ).toReversed();

  const bannerAwards = awardsSortedByEventDate
    .filter((a) => BLUE_BANNER_AWARDS.has(a.award_type))
    .filter((a) =>
      SEASON_EVENT_TYPES.has(
        events.find((e) => e.key === a.event_key)?.event_type ?? -1,
      ),
    );

  return (
    <div className="flex flex-wrap sm:flex-nowrap">
      <div className="top-0 mr-4 pt-5 sm:sticky">
        <YearSelector
          currentLabel="History"
          triggerClassName="w-[180px]"
          options={[
            {
              label: 'History',
              to: `/team/${team.team_number}/history`,
              isCurrent: true,
            },
            {
              label: 'Stats',
              to: `/team/${team.team_number}/stats`,
            },
            ...yearsParticipated.map((y) => ({
              label: String(y),
              to: `/team/${team.team_number}/${y}`,
            })),
          ]}
        />
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

        <div className="flex flex-col gap-4 sm:flex-row">
          <Table className="w-auto">
            <TableHeader>
              <TableRow>
                <TableHead className="w-[6ch]">Year</TableHead>
                <TableHead className="w-[40ch]">Event</TableHead>
                <TableHead className="w-[40ch]">Awards</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {events.map((e, i) => (
                <Fragment key={e.key}>
                  {(i == 0 || events[i - 1].year !== e.year) && (
                    <TableRow>
                      <TableCell
                        rowSpan={
                          events.filter((e2) => e2.year === e.year).length + 1
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
          <div className="flex justify-center sm:block">
            {bannerAwards.length > 0 && (
              <div className="flex w-96 flex-row flex-wrap justify-center gap-2">
                {bannerAwards.map((a) => {
                  const event = events.find((e) => e.key === a.event_key);
                  if (event === undefined) {
                    return null;
                  }
                  return (
                    <AwardBanner
                      key={`${a.award_type}-${a.event_key}`}
                      award={a}
                      event={event}
                    />
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
