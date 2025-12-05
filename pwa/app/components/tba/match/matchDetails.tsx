import ScoreBreakdown2025 from 'app/components/tba/match/scoreBreakdown2025';
import { YoutubeEmbed } from 'app/components/tba/videoEmbeds';

import { Event, Match } from '~/api/tba/read';
import { isScoreBreakdown2025 } from '~/lib/rankingPoints';

export default function MatchDetails({
  match,
  event,
}: {
  match: Match;
  event: Event;
}) {
  let sbDiv = null;

  if (isScoreBreakdown2025(match.score_breakdown)) {
    sbDiv = (
      <ScoreBreakdown2025
        scoreBreakdown={match.score_breakdown}
        match={match}
      />
    );
  }

  return (
    <div className="flex flex-col gap-4 md:flex-row">
      <div className="order-2 w-full md:order-1 md:w-lg">{sbDiv}</div>
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
