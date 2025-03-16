import { Link } from 'react-router';

import MdiVideo from '~icons/mdi/video';

import { TeamSimple } from '~/api/v3';
import InlineIcon from '~/components/tba/inlineIcon';
import { Button } from '~/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { getEventDateString } from '~/lib/eventUtils';

export default function TeamListTable({ teams }: { teams: TeamSimple[] }) {
  return (
      <Table className="">
        <TableHeader>
          <TableRow>
            <TableHead>Team Number</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Location</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {teams.map((team) => (
            <TableRow key={team.key}>
              <TableCell className="w-3/12">
                <Link className="text-base" to={`/team/${team.team_number}`}>
                  {team.team_number}
                </Link>
              </TableCell>
              <TableCell className="w-5/12">
                <div>
                  {team.nickname}
                </div>
              </TableCell>
              <TableCell className="w-4/12">
                <div className="text-sm text-neutral-600">
                  {team.city}, {team.state_prov}, {team.country}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
  );
}
