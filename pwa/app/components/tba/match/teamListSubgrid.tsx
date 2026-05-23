import { VariantProps, cva } from 'class-variance-authority';

import { TeamLinkWithTooltip } from '~/components/tba/teamTooltip';
import { cn } from '~/lib/utils';

const teamListSubgridVariants = cva('flex items-center justify-center', {
  variants: {
    allianceColor: {
      red: 'bg-alliance-red-bg-faded',
      blue: 'bg-alliance-blue-bg-faded',
    },
    winner: {
      true: 'font-semibold',
      false: '',
    },
  },
  compoundVariants: [
    {
      winner: true,
      allianceColor: 'red',
      className: 'bg-alliance-red-bg',
    },
    {
      winner: true,
      allianceColor: 'blue',
      className: 'bg-alliance-blue-bg',
    },
  ],
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

const teamCellVariants = cva('flex items-center justify-center text-white', {
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
});

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
  return (
    <div {...props}>
      <TeamLinkWithTooltip
        teamKey={teamKey}
        year={year}
        disqualified={dq ?? false}
        surrogate={surrogate ?? false}
        className={cn(teamCellVariants({ dq, surrogate, focus }))}
      />
    </div>
  );
}
