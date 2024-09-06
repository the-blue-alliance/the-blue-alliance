import { Link } from '@remix-run/react';
import { type VariantProps, cva } from 'class-variance-authority';
import type React from 'react';

import BiTrophy from '~icons/bi/trophy';

import { EliminationAlliance } from '~/api/v3';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { cn } from '~/lib/utils';

import InlineIcon from './inlineIcon';

const rowVariants = cva('text-center', {
  variants: {
    variant: {
      winner: 'bg-yellow-100 font-bold shadow-inner shadow-yellow-200',
      finalist: 'bg-gray-100 shadow-inner shadow-gray-200',
      default: '',
    },
  },
  defaultVariants: {
    variant: 'default',
  },
});

interface AllianceTableRowProps
  extends React.HTMLAttributes<HTMLTableRowElement>,
    VariantProps<typeof rowVariants> {}

function AllianceTableRow({
  className,
  variant,
  ...props
}: AllianceTableRowProps): React.JSX.Element {
  return (
    <TableRow className={cn(rowVariants({ variant, className }))} {...props} />
  );
}

function extractAllianceNumber(input: string): string {
  // Regular expression to match "Alliance" followed by a space and one or more digits
  const regex = /^Alliance (\d+)$/;
  const match = regex.exec(input);

  if (match) {
    // If there's a match, return the captured number as a string
    return match[1];
  }

  return input;
}

export default function AllianceSelectionTable(props: {
  alliances: EliminationAlliance[];
}) {
  const allianceSize =
    Math.max(...props.alliances.map((a) => a.picks.length)) || 3;

  return (
    <>
      <div className="text-xl">Alliances</div>

      <Table className="table-fixed">
        <TableHeader>
          <TableRow className="*:h-8 *:font-bold">
            <TableHead>Alliance</TableHead>
            <TableHead>Captain</TableHead>
            {[...Array(allianceSize - 1).keys()].map((i) => (
              <TableHead key={i}>Pick {i + 1}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {props.alliances.map((a, idx) => (
            <AllianceTableRow
              key={a.name}
              variant={
                a.status?.level === 'f'
                  ? a.status.status === 'won'
                    ? 'winner'
                    : 'finalist'
                  : 'default'
              }
            >
              <TableCell className="">
                {a.status?.status === 'won' ? (
                  <InlineIcon className="relative right-[1ch] justify-center">
                    <BiTrophy />
                    {extractAllianceNumber(a.name ?? `${idx + 1}`)}
                  </InlineIcon>
                ) : (
                  <>{extractAllianceNumber(a.name ?? `${idx + 1}`)}</>
                )}
              </TableCell>

              {[...Array(allianceSize).keys()].map((i) =>
                a.picks.length > i ? (
                  <TableCell key={a.picks[i]}>
                    <Link to={`/team/${a.picks[i].substring(3)}`}>
                      {a.picks[i].substring(3)}
                    </Link>
                  </TableCell>
                ) : (
                  <TableCell key={`${a.name ?? 'Alliance'}-${i}`}>-</TableCell>
                ),
              )}
            </AllianceTableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}
