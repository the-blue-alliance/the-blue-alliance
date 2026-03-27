import { google, ics, outlook } from 'calendar-link';

import AppleIcon from '~icons/logos/apple';
import GoogleCalendarIcon from '~icons/logos/google-calendar';
import MoreHorizontalIcon from '~icons/lucide/ellipsis';
import OutlookIcon from '~icons/vscode-icons/file-type-outlook';

import { Event } from '~/api/tba/read';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu';
import { toCalendarEvent } from '~/lib/eventUtils';

export default function AddToCalendarLinks({
  event,
}: {
  event: Event;
}): React.JSX.Element {
  const calEvent = toCalendarEvent(event);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className="ml-1.5 inline-flex cursor-pointer items-center align-middle
          text-muted-foreground hover:text-foreground"
        title="Add to calendar"
        aria-label="Add to calendar"
      >
        <MoreHorizontalIcon className="size-4" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        <DropdownMenuLabel>Add to Calendar</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <a
            href={google(calEvent)}
            target="_blank"
            rel="noreferrer"
            className="cursor-pointer gap-2"
          >
            <GoogleCalendarIcon className="size-4" />
            Google Calendar
          </a>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <a
            href={ics(calEvent)}
            download={`${event.key}.ics`}
            className="cursor-pointer gap-2"
          >
            <AppleIcon className="size-4 dark:invert" />
            Apple Calendar
          </a>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <a
            href={outlook(calEvent)}
            target="_blank"
            rel="noreferrer"
            className="cursor-pointer gap-2"
          >
            <OutlookIcon className="size-4" />
            Outlook
          </a>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
