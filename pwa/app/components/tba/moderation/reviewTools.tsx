import { type JSX, useState } from 'react';
import { Temporal } from 'temporal-polyfill';

import { Button } from '~/components/ui/button';
import { Input } from '~/components/ui/input';

// Moderator dashboards that still live on the Jinja site. The retired Jinja
// review home linked to these; the PWA review home keeps them reachable.
export const WEBCAST_DASHBOARD_URL =
  'https://www.thebluealliance.com/mod/webcasts';
export const OFFSEASON_DASHBOARD_URL =
  'https://www.thebluealliance.com/mod/offseasons';

export function manageTeamMediaUrl(teamNumber: string, year: number): string {
  const team = encodeURIComponent(teamNumber);
  return `https://www.thebluealliance.com/mod?team=${team}&year=${year}#frc${team}`;
}

export function ReviewMediaTools(): JSX.Element {
  const [teamNumber, setTeamNumber] = useState('');
  const year = Temporal.Now.plainDateISO().year;
  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-lg font-medium">Review Media Tools</h2>
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          render={<a href={WEBCAST_DASHBOARD_URL}>Webcast Dashboard</a>}
        />
        <Input
          className="w-44"
          inputMode="numeric"
          pattern="[0-9]+"
          placeholder="Manage Team Media"
          aria-label="Manage Team Media"
          value={teamNumber}
          onChange={(e) => setTeamNumber(e.target.value)}
        />
        <Button
          variant="outline"
          size="sm"
          render={
            <a
              href={
                teamNumber ? manageTeamMediaUrl(teamNumber, year) : undefined
              }
            >
              Go
            </a>
          }
        />
      </div>
    </div>
  );
}

export function ReviewOffseasonTools(): JSX.Element {
  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-lg font-medium">Review Offseason Tools</h2>
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          render={<a href={OFFSEASON_DASHBOARD_URL}>Offseason Dashboard</a>}
        />
      </div>
    </div>
  );
}
