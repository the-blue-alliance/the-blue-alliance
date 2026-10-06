import { VariantProps, cva } from 'class-variance-authority';
import { cn } from 'cn';

import { TeamLinkWithTooltip } from '~/components/tba/teamTooltip';

const teamListSubgridVariants = cva('flex items-center justify-center', {
  variants: {
    allianceColor: {
      red: 'bg-alliance-red-loser',
      blue: 'bg-alliance-blue-loser',
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
      className: 'bg-alliance-red-winner',
    },
    {
      winner: true,
      allianceColor: 'blue',
      className: 'bg-alliance-blue-winner',
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
  favoriteTeamKeys?: string[];
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
  favoriteTeamKeys,
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
          favorite={favoriteTeamKeys?.includes(teamKey) ?? false}
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
  favorite: boolean;
}

function TeamCell({
  teamKey,
  year,
  dq,
  surrogate,
  focus,
  favorite,
  ...props
}: TeamCellProps) {
  return (
    <div {...props}>
      <span className="relative">
        <TeamLinkWithTooltip
          teamKey={teamKey}
          year={year}
          disqualified={dq ?? false}
          surrogate={surrogate ?? false}
          className={cn(teamCellVariants({ dq, surrogate, focus }))}
        />
        {favorite && (
          <span
            className="absolute -top-0.5 -right-1.5 size-1.5 rounded-full
              bg-yellow-500"
          >
            <span className="sr-only">Favorite team</span>
          </span>
        )}
      </span>
    </div>
  );
}
