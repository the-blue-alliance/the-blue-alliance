import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { Event, Match } from '~/api/tba/read';
import { getMatchZebraOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import { SimpleMatchRow } from '~/components/tba/match/matchRows';
import { ScoreBreakdown2015 } from '~/components/tba/match/scoreBreakdown2015';
import ScoreBreakdown2018 from '~/components/tba/match/scoreBreakdown2018';
import ScoreBreakdown2023 from '~/components/tba/match/scoreBreakdown2023';
import ScoreBreakdown2024 from '~/components/tba/match/scoreBreakdown2024';
import ScoreBreakdown2025 from '~/components/tba/match/scoreBreakdown2025';
import ZebraMotionWorks from '~/components/tba/match/zebraMotionWorks';
import { YoutubeEmbed } from '~/components/tba/videoEmbeds';
import { Checkbox } from '~/components/ui/checkbox';
import {
  isScoreBreakdown2015,
  isScoreBreakdown2018,
  isScoreBreakdown2023,
  isScoreBreakdown2024,
  isScoreBreakdown2025,
} from '~/lib/rankingPoints';

function formatMatchDate(timestamp: number, timezone: string): string {
  const date = new Date(timestamp * 1000);

  return date.toLocaleString('en-US', {
    timeZone: timezone,
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

function formatMatchTime(
  timestamp: number,
  timezone: string,
): React.JSX.Element {
  const date = new Date(timestamp * 1000);

  const time = date.toLocaleString('en-US', {
    timeZone: timezone,
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });

  return <span className="font-bold">{time}</span>;
}

function formatTimeDifference(
  actualTime: number,
  scheduledTime: number,
): string {
  const diffSeconds = actualTime - scheduledTime;
  const diffMinutes = Math.round(diffSeconds / 60);

  if (Math.abs(diffMinutes) < 1) {
    return 'on time';
  }

  if (diffMinutes > 0) {
    const hours = Math.floor(diffMinutes / 60);
    const minutes = diffMinutes % 60;

    if (hours > 0) {
      return minutes > 0 ? `${hours}h ${minutes}m late` : `${hours}h late`;
    }
    return `${diffMinutes}m late`;
  }

  const absMinutes = Math.abs(diffMinutes);
  const hours = Math.floor(absMinutes / 60);
  const minutes = absMinutes % 60;

  if (hours > 0) {
    return minutes > 0 ? `${hours}h ${minutes}m early` : `${hours}h early`;
  }
  return `${absMinutes}m early`;
}

export default function MatchDetails({
  match,
  event,
}: {
  match: Match;
  event: Event;
}) {
  const [showUserTimezone, setShowUserTimezone] = useState(false);

  const { data: zebraData } = useQuery(
    getMatchZebraOptions({ path: { match_key: match.key } }),
  );

  const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const eventTimezone = event.timezone ?? 'UTC';
  const timezonesMatch = userTimezone === eventTimezone;
  const displayTimezone = showUserTimezone ? userTimezone : eventTimezone;

  const matchTimestamp =
    match.actual_time ?? match.time ?? match.predicted_time;

  let sbDiv = null;

  if (isScoreBreakdown2025(match.score_breakdown)) {
    sbDiv = (
      <ScoreBreakdown2025
        scoreBreakdown={match.score_breakdown}
        match={match}
      />
    );
  }

  if (isScoreBreakdown2024(match.score_breakdown)) {
    sbDiv = (
      <ScoreBreakdown2024
        scoreBreakdown={match.score_breakdown}
        match={match}
      />
    );
  }

  if (isScoreBreakdown2023(match.score_breakdown)) {
    sbDiv = (
      <ScoreBreakdown2023
        scoreBreakdown={match.score_breakdown}
        match={match}
      />
    );
  }

  if (isScoreBreakdown2018(match.score_breakdown)) {
    sbDiv = (
      <ScoreBreakdown2018
        scoreBreakdown={match.score_breakdown}
        match={match}
      />
    );
  }

  if (isScoreBreakdown2015(match.score_breakdown)) {
    sbDiv = <ScoreBreakdown2015 scoreBreakdown={match.score_breakdown} />;
  }

  return (
    <div className="flex flex-col gap-4 md:flex-row">
      <div className="order-2 w-full md:order-1 md:w-lg">
        <div className="flex flex-col gap-2">
          <SimpleMatchRow match={match} year={event.year} />
          {sbDiv}
          <div className="flex flex-col gap-2 rounded-lg border bg-muted/50 p-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Match Times</h3>
              {!timezonesMatch && (
                <label
                  htmlFor="timezone-toggle"
                  className="flex cursor-pointer items-center gap-1.5 text-xs"
                >
                  <Checkbox
                    id="timezone-toggle"
                    checked={showUserTimezone}
                    onCheckedChange={(checked) =>
                      setShowUserTimezone(checked === true)
                    }
                  />
                  <span>Show in my timezone</span>
                </label>
              )}
            </div>
            <div className="flex flex-col gap-1 text-xs">
              {matchTimestamp && (
                <div className="flex gap-1">
                  <span className="w-20 font-medium">Date:</span>
                  {formatMatchDate(matchTimestamp, displayTimezone)}
                </div>
              )}
              {match.actual_time && (
                <div className="flex gap-1">
                  <span className="w-20 font-medium">Actual:</span>
                  <span>
                    {formatMatchTime(match.actual_time, displayTimezone)}
                    {match.time && (
                      <span className="text-muted-foreground">
                        {' '}
                        ({formatTimeDifference(match.actual_time, match.time)})
                      </span>
                    )}
                  </span>
                </div>
              )}
              {match.time && (
                <div className="flex gap-1">
                  <span className="w-20 font-medium">Scheduled:</span>
                  {formatMatchTime(match.time, displayTimezone)}
                </div>
              )}
              {match.predicted_time && (
                <div className="flex gap-1">
                  <span className="w-20 font-medium">Predicted:</span>
                  {formatMatchTime(match.predicted_time, displayTimezone)}
                </div>
              )}
            </div>
          </div>
          {zebraData && <ZebraMotionWorks zebra={zebraData} />}
        </div>
      </div>
      <div className="order-1 flex w-full flex-col gap-2 md:order-2 md:w-xl">
        {match.videos
          .filter((v) => v.type === 'youtube')
          .map((v) => (
            <YoutubeEmbed
              key={v.key}
              videoId={v.key}
              title={`${event.name} ${match.match_number} ${v.key}`}
            />
          ))}
      </div>
    </div>
  );
}
