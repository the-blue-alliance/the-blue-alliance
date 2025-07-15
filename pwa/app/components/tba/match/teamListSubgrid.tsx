import { VariantProps, cva } from 'class-variance-authority';

import { TeamLink } from '~/components/tba/links';
import { cn } from '~/lib/utils';

const teamListSubgridVariants = cva('flex items-center justify-center', {
  variants: {
    allianceColor: {
      red: `bg-alliance-red-light first:rounded-tl-lg last:rounded-tr-lg
      xl:first:rounded-l-lg xl:last:rounded-r-lg`,
      blue: `bg-alliance-blue-light first:rounded-bl-lg last:rounded-br-lg
      xl:first:rounded-l-lg xl:last:rounded-r-lg`,
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
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof teamListSubgridVariants> {
  allianceColor: 'red' | 'blue';
  teamKeys: string[];
  dq: string[];
  surrogate: string[];
}

export default function TeamListSubgrid({
  allianceColor,
  className,
  teamKeys,
  winner,
  dq,
  surrogate,
  ...props
}: TeamListSubgridProps) {
  return (
    <div className={cn('grid grid-cols-3', className)} {...props}>
      {teamKeys.map((teamKey, index) => (
        <TeamCell
          key={index}
          teamKey={teamKey}
          dq={dq.includes(teamKey)}
          surrogate={surrogate.includes(teamKey)}
          className={cn(
            teamListSubgridVariants({
              allianceColor,
              winner,
            }),
          )}
        />
      ))}
    </div>
  );
}

const teamCellVariants = cva('flex items-center justify-center', {
  variants: {
    dq: {
      true: 'line-through',
      false: '',
    },
    surrogate: {
      true: 'underline',
      false: '',
    },
  },
  defaultVariants: {
    dq: false,
    surrogate: false,
  },
});

interface TeamCellProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof teamCellVariants> {
  teamKey: string;
}

function TeamCell({ teamKey, dq, surrogate, ...props }: TeamCellProps) {
  return (
    <div {...props}>
      <TeamLink teamOrKey={teamKey}>
        <span className={cn(teamCellVariants({ dq, surrogate }))}>
          {teamKey.substring(3)}
        </span>
      </TeamLink>
    </div>
  );
}
