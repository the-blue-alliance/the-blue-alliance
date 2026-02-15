import { createFileRoute } from '@tanstack/react-router';
import type { ReactNode } from 'react';

import { NotablesInsight } from '~/api/tba/read';
import { getInsightsNotablesYearOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import { EventLink, TeamLink } from '~/components/tba/links';
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { joinComponents, publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/hall-of-fame')({
  loader: async ({ context: { queryClient } }) => {
    const notables = await queryClient.ensureQueryData(
      getInsightsNotablesYearOptions({ path: { year: 0 } }),
    );

    return { notables };
  },
  headers: publicCacheControlHeaders(),
  head: () => ({
    meta: [
      { title: 'Hall of Fame - The Blue Alliance' },
      {
        name: 'description',
        content:
          "The FIRST Robotics Competition Hall of Fame recognizes teams that have won the Chairman's Award / FIRST Impact Award at the Championship level.",
      },
    ],
  }),
  component: HallOfFamePage,
});

function HallOfFamePage() {
  const { notables } = Route.useLoaderData();

  const hofNotable = notables.find(
    (n: NotablesInsight) => n.name === 'notables_hall_of_fame',
  );

  const worldChampionsNotable = notables.find(
    (n: NotablesInsight) => n.name === 'notables_world_champions',
  );

  if (!hofNotable) {
    return (
      <div className="py-8">
        <h1 className="mb-4 text-3xl font-medium">Hall of Fame</h1>
        <p className="text-muted-foreground">
          Hall of Fame data is not available.
        </p>
      </div>
    );
  }

  // Sort by number of wins (context.length), then by team number
  const sortedEntries = [...hofNotable.data.entries].sort((a, b) => {
    if (b.context.length !== a.context.length) {
      return b.context.length - a.context.length;
    }
    return (
      parseInt(a.team_key.substring(3)) - parseInt(b.team_key.substring(3))
    );
  });

  return (
    <div className="py-8">
      <h1 className="mb-2 text-3xl font-medium">Hall of Fame</h1>
      <p className="mb-6 text-muted-foreground">
        Teams inducted into the FIRST Robotics Competition Hall of Fame by
        winning the Chairman&apos;s Award / FIRST Impact Award at the
        Championship level.
      </p>

      <HallOfFameTable entries={sortedEntries} />

      {worldChampionsNotable && (
        <div className="mt-8">
          <h2 className="mb-2 text-2xl font-medium">World Champions</h2>
          <p className="mb-4 text-muted-foreground">
            Teams that have won the FIRST Championship.
          </p>
          <WorldChampionsTable entries={worldChampionsNotable.data.entries} />
        </div>
      )}
    </div>
  );
}

function HallOfFameTable({
  entries,
}: {
  entries: NotablesInsight['data']['entries'];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{entries.length} Hall of Fame Teams</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[80px]">Team</TableHead>
              <TableHead className="w-[60px] text-center">Wins</TableHead>
              <TableHead>Events</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.map((entry) => (
              <TableRow key={entry.team_key}>
                <TableCell>
                  <TeamLink teamOrKey={entry.team_key}>
                    {entry.team_key.substring(3)}
                  </TeamLink>
                </TableCell>
                <TableCell className="text-center">
                  {entry.context.length}
                </TableCell>
                <TableCell>
                  <EventContextList context={entry.context} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function WorldChampionsTable({
  entries,
}: {
  entries: NotablesInsight['data']['entries'];
}) {
  const sortedEntries = [...entries].sort((a, b) => {
    if (b.context.length !== a.context.length) {
      return b.context.length - a.context.length;
    }
    return (
      parseInt(a.team_key.substring(3)) - parseInt(b.team_key.substring(3))
    );
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {sortedEntries.length} World Championship Winning Teams
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[80px]">Team</TableHead>
              <TableHead className="w-[60px] text-center">Wins</TableHead>
              <TableHead>Events</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedEntries.map((entry) => (
              <TableRow key={entry.team_key}>
                <TableCell>
                  <TeamLink teamOrKey={entry.team_key}>
                    {entry.team_key.substring(3)}
                  </TeamLink>
                </TableCell>
                <TableCell className="text-center">
                  {entry.context.length}
                </TableCell>
                <TableCell>
                  <EventContextList context={entry.context} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function EventContextList({ context }: { context: string[] }): ReactNode {
  return joinComponents(
    context.map((eventKey) => (
      <EventLink key={eventKey} eventOrKey={eventKey}>
        {eventKey}
      </EventLink>
    )),
    ', ',
  );
}
