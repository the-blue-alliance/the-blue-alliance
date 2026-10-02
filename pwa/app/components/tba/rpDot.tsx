import { cn } from 'cn';

import { Match } from '~/api/tba/read';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import {
  RANKING_POINT_LABELS,
  getBonusRankingPoints,
} from '~/lib/rankingPoints';

export default function RpDots({
  score_breakdown,
  year,
}: {
  score_breakdown: NonNullable<Match['score_breakdown']>['red'];
  year: number;
}) {
  const rpsAchieved = getBonusRankingPoints(score_breakdown);
  if (rpsAchieved.length === 0) {
    return null;
  }

  const tooltipTexts = RANKING_POINT_LABELS[year] ?? [];
  const ariaLabel = rpsAchieved
    .map(
      (achieved, index) =>
        `${tooltipTexts[index] ?? 'Ranking Point'} (${achieved ? 'Achieved' : 'Not Achieved'})`,
    )
    .join(', ');

  return (
    <Tooltip>
      <TooltipTrigger
        delay={0}
        aria-label={ariaLabel}
        className="absolute top-[2px] left-[6px] flex cursor-pointer gap-[2px]
          border-0 p-0 after:absolute after:-top-[2px] after:-right-3
          after:-bottom-3 after:-left-[6px] after:content-['']
          focus:outline-none"
      >
        {rpsAchieved.map((achieved, index) => (
          <svg
            key={index}
            className="pointer-events-none size-1"
            viewBox="0 0 5 5"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle
              cx={2.5}
              cy={2.5}
              r={achieved ? 2.5 : 2}
              fill={achieved ? 'currentColor' : 'none'}
              stroke={achieved ? 'none' : '#9ca3af'}
              strokeWidth={achieved ? 0 : 1}
            />
          </svg>
        ))}
      </TooltipTrigger>
      <TooltipContent sideOffset={4}>
        <div className="flex flex-col gap-1 text-left">
          {rpsAchieved.map((achieved, index) => (
            <div key={index} className="flex items-center gap-1.5 text-xs">
              <svg
                className="size-1.5 shrink-0"
                viewBox="0 0 5 5"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <circle
                  cx={2.5}
                  cy={2.5}
                  r={achieved ? 2.5 : 2}
                  fill={achieved ? 'currentColor' : 'none'}
                  stroke={achieved ? 'none' : 'currentColor'}
                  strokeWidth={achieved ? 0 : 1}
                  className={achieved ? '' : 'opacity-50'}
                />
              </svg>
              <span
                className={cn(
                  'font-normal whitespace-nowrap',
                  !achieved && 'text-muted-foreground',
                )}
              >
                {tooltipTexts[index] ?? 'Ranking Point'}
              </span>
            </div>
          ))}
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
