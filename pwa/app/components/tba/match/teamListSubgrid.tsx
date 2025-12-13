import { VariantProps, cva } from 'class-variance-authority';

import { TeamLink } from '~/components/tba/links';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import { cn } from '~/lib/utils';

const teamListSubgridVariants = cva('flex items-center justify-center', {
  variants: {
    allianceColor: {
      red: `mt-0.5 bg-alliance-red/10 max-xl:first:rounded-tl-lg
      max-xl:last:rounded-tr-lg xl:mb-0.5 xl:first:rounded-l-lg`,
      blue: `mb-0.5 bg-alliance-blue/10 max-xl:mb-0.5 max-xl:first:rounded-bl-lg
      max-xl:last:rounded-br-lg xl:mt-0.5 xl:last:rounded-r-lg`,
    },
    winner: {
      true: 'font-semibold',
      false: '',
    },
  },
  defaultVariants: {
    allianceColor: undefined,
    winner: false,
  },
});

interface TeamListSubgridProps
  extends
    React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof teamListSubgridVariants> {
  allianceColor: 'red' | 'blue';
  teamKeys: string[];
  dq: string[];
  surrogate: string[];
  year: number;
  focusTeamKey?: string;
  teamCellClassName?: string;
}

export default function TeamListSubgrid({
  allianceColor,
  className,
  teamKeys,
  winner,
  dq,
  surrogate,
  year,
  focusTeamKey,
  teamCellClassName,
  ...props
}: TeamListSubgridProps) {
  return (
    <div className={cn('grid grid-cols-3', className)} {...props}>
      {teamKeys.map((teamKey, index) => (
        <TeamCell
          key={index}
          teamKey={teamKey}
          year={year}
          dq={dq.includes(teamKey)}
          surrogate={surrogate.includes(teamKey)}
          focus={focusTeamKey === teamKey}
          className={cn(
            teamListSubgridVariants({
              allianceColor,
              winner,
            }),
            teamCellClassName,
          )}
        />
      ))}
    </div>
  );
}

const teamCellVariants = cva(
  'flex items-center justify-center text-foreground',
  {
    variants: {
      dq: {
        true: 'line-through',
        false: '',
      },
      surrogate: {
        true: 'underline decoration-dashed',
        false: '',
      },
      focus: {
        true: 'underline',
        false: '',
      },
    },
    defaultVariants: {
      dq: false,
      surrogate: false,
      focus: false,
    },
  },
);

interface TeamCellProps
  extends
    React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof teamCellVariants> {
  teamKey: string;
  year: number;
}

function TeamCell({
  teamKey,
  year,
  dq,
  surrogate,
  focus,
  ...props
}: TeamCellProps) {
  const content = (
    <TeamLink
      teamOrKey={teamKey}
      year={year}
      className={cn(teamCellVariants({ dq, surrogate, focus }))}
    >
      {teamKey.substring(3)}
    </TeamLink>
  );

  if (dq || surrogate) {
    return (
      <div {...props}>
        <Tooltip>
          <TooltipTrigger asChild>{content}</TooltipTrigger>
          <TooltipContent>{dq ? 'DQ' : 'Surrogate'}</TooltipContent>
        </Tooltip>
      </div>
    );
  }

  return <div {...props}>{content}</div>;
}
