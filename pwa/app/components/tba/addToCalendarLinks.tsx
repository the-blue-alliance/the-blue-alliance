import { google, ics } from 'calendar-link';

import AppleIcon from '~icons/logos/apple';
import GoogleCalendarIcon from '~icons/logos/google-calendar';

import { Event } from '~/api/tba/read';
import { toCalendarEvent } from '~/lib/eventUtils';

export default function AddToCalendarLinks({
  event,
}: {
  event: Event;
}): React.JSX.Element {
  const calEvent = toCalendarEvent(event);

  return (
    <span className="ml-1.5 inline-flex gap-1.5 align-middle">
      <a
        href={google(calEvent)}
        target="_blank"
        rel="noreferrer"
        title="Add to Google Calendar"
      >
        <GoogleCalendarIcon />
      </a>
      <a
        href={ics(calEvent)}
        download={`${event.key}.ics`}
        title="Add to Apple Calendar"
        className="dark:invert"
      >
        <AppleIcon />
      </a>
    </span>
  );
}
