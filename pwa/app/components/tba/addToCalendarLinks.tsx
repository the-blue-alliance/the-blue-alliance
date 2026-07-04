import { google, ics, outlook } from 'calendar-link';

import AppleIcon from '~icons/logos/apple';
import GoogleCalendarIcon from '~icons/logos/google-calendar';
import MoreHorizontalIcon from '~icons/lucide/ellipsis';
import OutlookIcon from '~icons/vscode-icons/file-type-outlook';

import { Event } from '~/api/tba/read';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
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
        <DropdownMenuGroup>
          <DropdownMenuLabel>Add to Calendar</DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            render={
              // eslint-disable-next-line jsx-a11y/anchor-has-content -- content comes from DropdownMenuItem's own children, merged onto this element by Base UI's render prop
              <a
                href={google(calEvent)}
                target="_blank"
                rel="noreferrer"
                className="cursor-pointer gap-2"
              />
            }
          >
            <GoogleCalendarIcon className="size-4" />
            Google Calendar
          </DropdownMenuItem>
          <DropdownMenuItem
            render={
              // eslint-disable-next-line jsx-a11y/anchor-has-content -- content comes from DropdownMenuItem's own children, merged onto this element by Base UI's render prop
              <a
                href={ics(calEvent)}
                download={`${event.key}.ics`}
                className="cursor-pointer gap-2"
              />
            }
          >
            <AppleIcon className="size-4 dark:invert" />
            Apple Calendar
          </DropdownMenuItem>
          <DropdownMenuItem
            render={
              // eslint-disable-next-line jsx-a11y/anchor-has-content -- content comes from DropdownMenuItem's own children, merged onto this element by Base UI's render prop
              <a
                href={outlook(calEvent)}
                target="_blank"
                rel="noreferrer"
                className="cursor-pointer gap-2"
              />
            }
          >
            <OutlookIcon className="size-4" />
            Outlook
          </DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
