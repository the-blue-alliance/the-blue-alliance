import { Match } from '~/api/tba/read';
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

function RpDot({
  tooltipText,
  achieved,
}: {
  tooltipText: string;
  achieved: boolean;
}) {
  return (
    <TooltipProvider delayDuration={100}>
      <Tooltip>
        <TooltipTrigger asChild>
          <svg className="h-[5px] w-[5px]">
            <circle
              cx={2.5}
              cy={2.5}
              r={achieved ? 2.5 : 2}
              fill={achieved ? 'currentColor' : 'none'}
              stroke={achieved ? 'none' : '#9ca3af'}
              strokeWidth={achieved ? 0 : 1}
            />
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
    <div className="absolute top-[2px] left-[3px] flex gap-[2px]">
      {rpsAchieved.map((achieved, index) => (
        <RpDot
          key={index}
          tooltipText={tooltipTexts[index]}
          achieved={achieved}
        />
      ))}
    </div>
  );
}
