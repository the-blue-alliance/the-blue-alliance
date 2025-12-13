import { Link } from '@tanstack/react-router';

import { TeamSimple } from '~/api/tba/read';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';

export default function TeamListTable({ teams }: { teams: TeamSimple[] }) {
  return (
    <Table className="w-full">
      <TableHeader>
        <TableRow>
          <TableHead>Number</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Location</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {teams.map((team) => (
          <TableRow key={team.key}>
            <TableCell className="w-2/12">
              <Link
                className="w-full text-base"
                to="/team/$teamNumber/{-$year}"
                params={{
                  teamNumber: team.team_number.toString(),
                }}
              >
                {team.team_number}
              </Link>
            </TableCell>
            <TableCell className="w-6/12 truncate">{team.nickname}</TableCell>
            <TableCell className="w-4/12">
              {team.city != null && (
                <div className="text-sm text-neutral-600">
                  {team.city}, {team.state_prov}, {team.country}
                </div>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
