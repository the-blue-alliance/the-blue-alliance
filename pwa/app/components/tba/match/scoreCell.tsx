import { VariantProps, cva } from 'class-variance-authority';

import { CompLevel, Match } from '~/api/tba/read';
import RpDots from '~/components/tba/rpDot';
import { cn } from '~/lib/utils';

const scoreCellVariants = cva(
  'relative flex items-center justify-center numeric-data',
  {
    variants: {
      winner: {
        true: 'font-semibold',
        false: '',
      },
      allianceColor: {
        red: 'bg-alliance-red-loser',
        blue: 'bg-alliance-blue-loser',
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
      winner: false,
      allianceColor: undefined,
    },
  },
);

interface ScoreCellProps
  extends
    React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof scoreCellVariants> {
  score: number;
  scoreBreakdown?: NonNullable<Match['score_breakdown']>['red'];
  year?: number;
  compLevel: Match['comp_level'];
  focused?: boolean;
}

export default function ScoreCell({
  score,
  winner,
  allianceColor,
  scoreBreakdown,
  year,
  compLevel,
  focused,
  className,
  ...props
}: ScoreCellProps) {
  return (
    <div
      className={cn(
        scoreCellVariants({ winner, allianceColor }),
        focused && 'underline',
        className,
      )}
      {...props}
    >
      {scoreBreakdown && year && compLevel === CompLevel.QM && (
        <RpDots score_breakdown={scoreBreakdown} year={year} />
      )}
      {score}
    </div>
  );
}
