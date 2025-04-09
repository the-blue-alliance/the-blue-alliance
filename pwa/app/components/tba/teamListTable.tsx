import { Link } from 'react-router';

import { TeamSimple } from '~/api/v3';
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
    <Table>
      <TableHeader className="">
        <TableRow>
          <TableHead>Number</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Location</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {teams.map((team) => (
          <TableRow key={team.key}>
            <TableCell className="flex w-2/12 justify-center">
              <Link
                className="w-full text-base"
                to={`/team/${team.team_number}`}
              >
                {team.team_number}
              </Link>
            </TableCell>
            <TableCell className="w-5/12">
              <div>
                {team.nickname.length > 52
                  ? team.nickname.slice(0, 52).concat('...')
                  : team.nickname}
              </div>
            </TableCell>
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
