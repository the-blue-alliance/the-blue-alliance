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
      red: `mt-0.5 bg-alliance-red/15 max-lg:rounded-t-lg xl:mb-0.5
      xl:rounded-l-lg`,
      blue: `mb-0.5 bg-alliance-blue/15 max-lg:rounded-b-lg xl:mt-0.5
      xl:rounded-r-lg`,
    },
  },
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
