import { VariantProps, cva } from 'class-variance-authority';

import { Match } from '~/api/tba/read';
import RpDots from '~/components/tba/rpDot';
import { cn } from '~/lib/utils';

const scoreCellVariants = cva('relative flex items-center justify-center', {
  variants: {
    winner: {
      true: 'font-semibold',
      false: '',
    },
    allianceColor: {
      red: 'bg-alliance-red-cell',
      blue: 'bg-alliance-blue-cell',
    },
  },
  compoundVariants: [
    {
      winner: true,
      allianceColor: 'red',
      className: 'bg-alliance-red-cell-winner',
    },
    {
      winner: true,
      allianceColor: 'blue',
      className: 'bg-alliance-blue-cell-winner',
    },
  ],
  defaultVariants: {
    winner: false,
    allianceColor: undefined,
  },
});

interface ScoreCellProps
  extends
    React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof scoreCellVariants> {
  score: number;
  scoreBreakdown?: NonNullable<Match['score_breakdown']>['red'];
  year?: number;
  compLevel: Match['comp_level'];
}

export default function ScoreCell({
  score,
  winner,
  allianceColor,
  scoreBreakdown,
  year,
  compLevel,
  className,
  ...props
}: ScoreCellProps) {
  return (
    <div
      className={cn(scoreCellVariants({ winner, allianceColor }), className)}
      {...props}
    >
      {scoreBreakdown && year && compLevel === 'qm' && (
        <RpDots score_breakdown={scoreBreakdown} year={year} />
      )}
      {score}
    </div>
  );
}
