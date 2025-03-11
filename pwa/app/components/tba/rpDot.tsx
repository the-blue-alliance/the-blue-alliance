import { Match } from '~/api/v3';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import {
  RANKING_POINT_LABELS,
  getBonusRankingPoints,
} from '~/lib/rankingPoints';
import { cn } from '~/lib/utils';

function RpDot({
  rpIndex,
  tooltipText,
}: {
  rpIndex: number;
  tooltipText: string;
}) {
  return (
    <TooltipProvider delayDuration={100}>
      <Tooltip>
        <TooltipTrigger asChild>
          <svg
            className={cn('absolute top-[2px] left-[3px] h-[4px] w-[4px]', {
              'ml-0': rpIndex === 0,
              'ml-[6px]': rpIndex === 1,
              'ml-[12px]': rpIndex === 2,
            })}
          >
            <circle cx={2} cy={2} r={2} />
          </svg>
        </TooltipTrigger>
        <TooltipContent>
          <span className="font-normal">{tooltipText}</span>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export default function RpDots({
  score_breakdown,
  year,
}: {
  score_breakdown: NonNullable<Match['score_breakdown']>['red'];
  year: number;
}) {
  const rpsAchieved = getBonusRankingPoints(score_breakdown);
  const tooltipTexts = RANKING_POINT_LABELS[year];

  return (
    <>
      {rpsAchieved.map((rp, index) =>
        rp ? (
          <RpDot
            key={index}
            rpIndex={index}
            tooltipText={tooltipTexts[index]}
          />
        ) : null,
      )}
    </>
  );
}
