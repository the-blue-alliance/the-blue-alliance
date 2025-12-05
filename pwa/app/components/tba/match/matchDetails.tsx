import { Event, Match } from '~/api/tba/read';

export default function MatchDetails({
  match,
  event,
}: {
  match: Match;
  event: Event;
}) {
  return (
    <div>
      {event.key} - {match.key}
    </div>
  );
}
