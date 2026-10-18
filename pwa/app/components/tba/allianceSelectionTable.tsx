import { type VariantProps, cva } from 'class-variance-authority';
import { cn } from 'cn';
import { type HTMLAttributes, type JSX } from 'react';

import BiTrophy from '~icons/bi/trophy';

import { EliminationAlliance, Match } from '~/api/tba/read';
import InlineIcon from '~/components/tba/inlineIcon';
import { TeamLinkWithTooltip } from '~/components/tba/teamTooltip';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { getFinalsResult } from '~/lib/matchUtils';
import { remapTeamKeys } from '~/lib/teamRemap';

const rowVariants = cva('text-center', {
  variants: {
    variant: {
      winner: `bg-yellow-100! font-bold shadow-inner shadow-yellow-200
      dark:bg-yellow-500/15! dark:shadow-yellow-500/10`,
      finalist:
        'bg-neutral-100! shadow-inner shadow-border dark:bg-neutral-800!',
      default: '',
    },
  },
  defaultVariants: {
    variant: 'default',
  },
});

interface AllianceTableRowProps
  extends
    HTMLAttributes<HTMLTableRowElement>,
    VariantProps<typeof rowVariants> {}

function AllianceTableRow({
  className,
  variant,
  ...props
}: AllianceTableRowProps): JSX.Element {
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
  matches: Match[];
  eventOver: boolean;
  year: number;
  remapTeams?: Record<string, string> | null;
}) {
  const { winner, finalists } = getFinalsResult(
    props.alliances,
    props.matches,
    props.eventOver,
  );
  const alliances = props.alliances.map((a) => ({
    ...a,
    picks: remapTeamKeys(a.picks, props.remapTeams),
    variant:
      a === winner
        ? ('winner' as const)
        : finalists.includes(a)
          ? ('finalist' as const)
          : ('default' as const),
  }));
  const allianceSize =
    Math.max(0, ...alliances.map((a) => a.picks.length)) || 3;

  return (
    <>
      <h2 className="mb-2 text-xl font-medium">Alliances</h2>

      <Table className="table-fixed">
        <TableHeader>
          <TableRow className="*:h-8 *:text-center *:text-foreground">
            <TableHead>Alliance</TableHead>
            <TableHead>Captain</TableHead>
            {allianceSize > 1 &&
              [...Array(allianceSize - 1).keys()].map((i) => (
                <TableHead key={i}>Pick {i + 1}</TableHead>
              ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {alliances.map((a, idx) => (
            <AllianceTableRow
              key={`alliance-${idx}`}
              className="odd:bg-transparent"
              variant={a.variant}
            >
              <TableCell className="">
                {a.variant === 'winner' ? (
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
                    <TeamLinkWithTooltip
                      teamKey={a.picks[i]}
                      year={props.year}
                    />
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
