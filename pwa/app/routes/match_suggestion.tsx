import * as ProgressPrimitive from '@radix-ui/react-progress';
import { useQuery } from '@tanstack/react-query';
import React, { useState } from 'react';
import { useLoaderData } from 'react-router';

import {
  Event,
  EventRanking,
  Match,
  getEvent,
  getEventMatches,
  getEventPredictions,
  getEventRankings,
  getEventsByYear,
  getInsightsNotablesYear,
  getStatus,
  getTeam,
  getTeamEventsStatusesByYear,
} from '~/api/v3';
import { TeamLink } from '~/components/tba/links';
import { MatchResultsTableGroup } from '~/components/tba/matchResultsTable';
import { Badge } from '~/components/ui/badge';
import { getCurrentWeekEvents } from '~/lib/eventUtils';
import { matchTitleShort, sortMatchComparator } from '~/lib/matchUtils';
import { cn, queryFromAPI } from '~/lib/utils';

export async function loader() {
  const status = await getStatus({});

  if (status.status !== 200) {
    throw new Response(null, {
      status: 500,
    });
  }

  const year = status.data.current_season;
  const events = await getEventsByYear({ year });

  if (events.status !== 200) {
    throw new Response(null, {
      status: 500,
    });
  }

  const filteredEvents = getCurrentWeekEvents(events.data);

  return {
    events: filteredEvents,
  };
}

// TODO: Fix this typing
type EventPredictions = {
  match_predictions: {
    qual: {
      [key: string]: {
        red: {
          score: number;
          coral_scored: number;
          barge_points: number;
        };
        blue: {
          score: number;
          coral_scored: number;
          barge_points: number;
        };
      };
    };
    playoff: {
      [key: string]: {
        red: { score: number; coral_scored: number; barge_points: number };
        blue: { score: number; coral_scored: number; barge_points: number };
      };
    };
  };
};

interface MatchInfo {
  match: Match;
  event: Event;
  eventRankings?: EventRanking | null;
  eventPredictions?: EventPredictions | null;
}

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>
>(({ className, value, ...props }, ref) => (
  <ProgressPrimitive.Root
    ref={ref}
    className={cn(
      'relative h-4 w-full overflow-hidden rounded-full bg-secondary',
      className,
    )}
    {...props}
  >
    <ProgressPrimitive.Indicator
      className="size-full flex-1 bg-primary transition-all"
      style={{ transform: `translateX(-${100 - (value ?? 0)}%)` }}
    />
  </ProgressPrimitive.Root>
));
Progress.displayName = ProgressPrimitive.Root.displayName;

function EventName({ eventKey }: { eventKey: string }) {
  const eventQuery = useQuery({
    queryKey: ['event', eventKey],
    queryFn: () => queryFromAPI(getEvent({ eventKey })),
  });
  if (!eventQuery.data) {
    return eventKey;
  }
  return eventQuery.data.name;
}

function TeamDetails({
  teamKey,
  className,
}: {
  teamKey: string;
  className: string;
}) {
  const teamQuery = useQuery({
    queryKey: ['team', teamKey],
    queryFn: () => queryFromAPI(getTeam({ teamKey })),
  });
  const eventStatusesQuery = useQuery({
    queryKey: ['teamEventStatusByYear', teamKey, 2025],
    queryFn: () =>
      queryFromAPI(getTeamEventsStatusesByYear({ teamKey, year: 2025 })),
  });

  const insightNotablesYearQuery = useQuery({
    queryKey: ['insightNotablesYear', 0],
    queryFn: () => queryFromAPI(getInsightsNotablesYear({ year: 0 })),
  });
  const divisionWinnersNotable =
    insightNotablesYearQuery.data &&
    insightNotablesYearQuery.data
      .find((insight) => insight.name == 'notables_division_winners')
      ?.data.entries.find((notable) => notable.team_key == teamKey);

  if (
    !teamQuery.data ||
    !eventStatusesQuery.data ||
    !insightNotablesYearQuery.data
  ) {
    return (
      <td className={cn('text-left', className)} colSpan={2}>
        Loading...
      </td>
    );
  }

  const divisionWins = divisionWinnersNotable
    ? divisionWinnersNotable.context.map((eventKey) => eventKey.substring(0, 4))
    : [];

  const statuses = [];
  for (const [key, value] of Object.entries(eventStatusesQuery.data)) {
    statuses.push({
      event: key,
      rank: value?.qual?.ranking?.rank,
      alliance: value?.alliance
        ? `A${value.alliance.number}P${value.alliance.pick || 'C'}`
        : 'DNP',
      finish:
        value?.playoff?.status == 'won'
          ? 'Winner'
          : value?.playoff?.level == 'f'
            ? 'Finalist'
            : '?',
    });
  }

  return (
    <td className={cn('text-left', className)} colSpan={2}>
      <div className="text-lg">
        Team {teamQuery.data.team_number} - {teamQuery.data.nickname}
      </div>
      <hr />
      <div>
        {teamQuery.data.city}, {teamQuery.data.state_prov},{' '}
        {teamQuery.data.country}
      </div>
      <hr />
      {statuses.map((status) => (
        <div key={status.event} className="py-2">
          <div>
            <b>Event:</b> <EventName eventKey={status.event} />
          </div>
          <div>
            <b>Rank:</b> {status.rank}
          </div>
          <div>
            <b>Alliance:</b> {status.alliance}
          </div>
          <div>
            <b>Finish:</b> {status.finish}
          </div>
        </div>
      ))}
      <hr />
      <div>
        <b>Past Einstein:</b>{' '}
        {divisionWins.length > 0 ? divisionWins.join(', ') : 'N/A'}
      </div>
    </td>
  );
}

function MatchSuggestionRow({
  match,
  event,
  eventRankings,
  eventPredictions,
}: MatchInfo) {
  const [showDetails, setShowDetails] = useState(false);

  const prediction =
    eventPredictions?.match_predictions.qual[match.key] ||
    eventPredictions?.match_predictions.playoff[match.key];

  const predictedRedScore = prediction ? prediction.red.score : 0.0;
  const predictedBlueScore = prediction ? prediction.blue.score : 0.0;

  const redGamePieceCount = prediction ? prediction.red.coral_scored : 0.0;
  const blueGamePieceCount = prediction ? prediction.blue.coral_scored : 0.0;

  const redEndGamePoints = prediction ? prediction.red.barge_points : 0.0;
  const blueEndGamePoints = prediction ? prediction.blue.barge_points : 0.0;

  const blueZoneScore =
    100 *
    Math.min(
      1.0,
      (Math.max(predictedRedScore, predictedBlueScore) +
        2.0 * Math.min(predictedRedScore, predictedBlueScore)) /
        750.0,
    );

  return (
    <>
      <tr key={match.key} className="text-center">
        <td className="border">{event.key.substring(4).toUpperCase()}</td>
        <td className="border">{matchTitleShort(match, event)}</td>
        <td className="border">
          {match.predicted_time && (
            <span>
              {new Date(match.predicted_time * 1000).toLocaleTimeString(
                'en-US',
                {
                  hour: '2-digit',
                  minute: '2-digit',
                  weekday: 'short',
                  hour12: true,
                },
              )}
            </span>
          )}
        </td>
        {match.alliances.red.team_keys.map((k) => (
          <td className="border bg-alliance-red-light" key={k}>
            <TeamLink teamOrKey={k} year={event.year}>
              {k.substring(3)}
            </TeamLink>
            <br />({eventRankings?.rankings.find((r) => r.team_key == k)?.rank})
          </td>
        ))}
        {match.alliances.blue.team_keys.map((k) => (
          <td className="border bg-alliance-blue-light" key={k}>
            <TeamLink teamOrKey={k} year={event.year}>
              {k.substring(3)}
            </TeamLink>
            <br />({eventRankings?.rankings.find((r) => r.team_key == k)?.rank})
          </td>
        ))}
        <td className="border bg-alliance-red-dark">
          {predictedRedScore.toFixed(0)}
        </td>
        <td className="border bg-alliance-blue-dark">
          {predictedBlueScore.toFixed(0)}
        </td>
        <td className="border bg-alliance-red-light">
          {redGamePieceCount.toFixed(0)}
          <Progress value={(redGamePieceCount / 69.0) * 100.0} />
        </td>
        <td className="border bg-alliance-blue-light">
          {blueGamePieceCount.toFixed(0)}
          <Progress value={(blueGamePieceCount / 69.0) * 100.0} />
        </td>
        <td className="border bg-alliance-red-light">
          {redEndGamePoints.toFixed(0)}
          <Progress value={(redEndGamePoints / 36.0) * 100.0} />
        </td>
        <td className="border bg-alliance-blue-light">
          {blueEndGamePoints.toFixed(0)}
          <Progress value={(blueEndGamePoints / 36.0) * 100.0} />
        </td>
        <td className="border">
          {blueZoneScore.toFixed(0)}
          <Progress value={blueZoneScore} />
        </td>
        <td className="border">
          <Badge
            className="ml-2 cursor-pointer"
            onClick={() => {
              setShowDetails((prev) => !prev);
            }}
          >
            {showDetails ? 'Hide' : 'Show'}
          </Badge>
        </td>
      </tr>
      {showDetails && (
        <tr>
          <td></td>
          <td></td>
          <td></td>
          {match.alliances.red.team_keys.map((k) => (
            <TeamDetails
              key={k}
              teamKey={k}
              className="bg-alliance-red-light"
            />
          ))}
          {match.alliances.blue.team_keys.map((k) => (
            <TeamDetails
              key={k}
              teamKey={k}
              className="bg-alliance-blue-light"
            />
          ))}
        </tr>
      )}
    </>
  );
}

export default function MatchSuggestion(): React.JSX.Element {
  const { events } = useLoaderData<typeof loader>();

  const eventMatchesQuery = useQuery({
    queryKey: ['eventMatches', events],
    queryFn: () =>
      Promise.all(
        events.map(async (event) =>
          (await queryFromAPI(getEventMatches({ eventKey: event.key }))).sort(
            sortMatchComparator,
          ),
        ),
      ),
  });

  const eventRankingsQuery = useQuery({
    queryKey: ['eventRankings', events],
    queryFn: () =>
      Promise.all(
        events.map(
          async (event) =>
            await queryFromAPI(getEventRankings({ eventKey: event.key })),
        ),
      ),
  });

  const eventPredictionsQuery = useQuery({
    queryKey: ['eventPredictions', events],
    queryFn: () =>
      Promise.all(
        events.map(
          async (event) =>
            await queryFromAPI(getEventPredictions({ eventKey: event.key })),
        ),
      ),
  });

  if (!eventMatchesQuery.data) {
    return <div>No matches!</div>;
  }

  const finishedMatches: Match[] = [];
  const currentMatches: MatchInfo[] = [];
  const upcomingMatches: MatchInfo[] = [];

  eventMatchesQuery.data.forEach((eventMatches, eventIdx) => {
    const lastMatch = eventMatches.findLast(
      (match) =>
        match.alliances.red.score != -1 && match.alliances.blue.score != -1,
    );
    if (lastMatch) {
      finishedMatches.push(lastMatch);
    }

    const unplayedMatches = eventMatches.filter(
      (match) =>
        match.alliances.red.score == -1 || match.alliances.blue.score == -1,
    );
    unplayedMatches.forEach((match, i) => {
      if (i > 2) {
        return;
      }
      if (i == 0) {
        currentMatches.push({
          match,
          event: events[eventIdx],
          eventRankings: eventRankingsQuery.data?.[eventIdx],
          eventPredictions: eventPredictionsQuery.data?.[
            eventIdx
          ] as EventPredictions,
        });
      } else {
        upcomingMatches.push({
          match,
          event: events[eventIdx],
          eventRankings: eventRankingsQuery.data?.[eventIdx],
          eventPredictions: eventPredictionsQuery.data?.[
            eventIdx
          ] as EventPredictions,
        });
      }
    });
  });

  finishedMatches.sort(
    (a, b) => (a.actual_time ?? a.time ?? 0) - (b.actual_time ?? b.time ?? 0),
  );
  currentMatches.sort(
    (a, b) =>
      (a.match.predicted_time ?? a.match.time ?? 0) -
      (b.match.predicted_time ?? b.match.time ?? 0),
  );
  upcomingMatches.sort(
    (a, b) =>
      (a.match.predicted_time ?? a.match.time ?? 0) -
      (b.match.predicted_time ?? b.match.time ?? 0),
  );

  return (
    <div className="absolute right-0 left-0 px-4 py-8">
      <h1 className="text-3xl font-medium">Match Suggestions</h1>
      <Badge
        className="ml-2 cursor-pointer"
        onClick={() => {
          void (async () => {
            await Promise.all([
              eventMatchesQuery.refetch(),
              eventRankingsQuery.refetch(),
              eventPredictionsQuery.refetch(),
            ]);
          })();
        }}
      >
        Refresh
      </Badge>
      <h2 className="text-2xl font-medium">Finished Matches</h2>
      {/* This is a hack for now. */}
      <MatchResultsTableGroup
        event={events[0]}
        matches={finishedMatches}
        showEvent
      />
      <h2 className="text-2xl font-medium">Current Matches</h2>
      <table className="w-[100%]">
        <thead>
          <tr>
            <th className="border">Event</th>
            <th className="border">Match</th>
            <th className="border">Time</th>
            <th className="border">R1 (Rank)</th>
            <th className="border">R2 (Rank)</th>
            <th className="border">R3 (Rank)</th>
            <th className="border">B1 (Rank)</th>
            <th className="border">B2 (Rank)</th>
            <th className="border">B3 (Rank)</th>
            <th className="border">Red Predicted Score</th>
            <th className="border">Blue Predicted Score</th>
            <th className="border">Red Game Piece Count</th>
            <th className="border">Blue Game Piece Count</th>
            <th className="border">Red Endgame Points</th>
            <th className="border">Blue Endgame Points</th>
            <th className="border">BlueZone Score</th>
            <th className="border">Details</th>
          </tr>
        </thead>
        <tbody>
          {currentMatches.map((matchInfo) => (
            <MatchSuggestionRow key={matchInfo.match.key} {...matchInfo} />
          ))}
        </tbody>
      </table>
      <h2 className="text-2xl font-medium">Upcoming Matches</h2>
      <table className="w-[100%]">
        <thead>
          <tr>
            <th className="border">Event</th>
            <th className="border">Match</th>
            <th className="border">Time</th>
            <th className="border">R1 (Rank)</th>
            <th className="border">R2 (Rank)</th>
            <th className="border">R3 (Rank)</th>
            <th className="border">B1 (Rank)</th>
            <th className="border">B2 (Rank)</th>
            <th className="border">B3 (Rank)</th>
            <th className="border">Red Predicted Score</th>
            <th className="border">Blue Predicted Score</th>
            <th className="border">Red Game Piece Count</th>
            <th className="border">Blue Game Piece Count</th>
            <th className="border">Red Endgame Points</th>
            <th className="border">Blue Endgame Points</th>
            <th className="border">BlueZone Score</th>
            <th className="border">Details</th>
          </tr>
        </thead>
        <tbody>
          {upcomingMatches.map((matchInfo) => (
            <MatchSuggestionRow key={matchInfo.match.key} {...matchInfo} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
