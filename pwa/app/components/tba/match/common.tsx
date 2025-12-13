import MdiCheck from '~icons/mdi/check';
import MdiClose from '~icons/mdi/close';

import { Badge } from '~/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';

export function ConditionalCheckmark({
  condition,
  teamKey,
}: {
  condition: boolean;
  teamKey: string;
}) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          {condition ? <MdiCheck /> : <MdiClose />}
        </TooltipTrigger>
        <TooltipContent>{teamKey}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export function ConditionalRpAchieved({ condition }: { condition: boolean }) {
  return (
    <div className="flex items-center justify-center">
      {condition ? <MdiCheck /> : <MdiClose />}
    </div>
  );
}

export function ConditionalBadge({
  condition,
  teamKey,
  alignIcon,
}: {
  condition: boolean;
  teamKey: string;
  alignIcon: 'left' | 'right';
}) {
  return (
    <Badge
      variant={condition ? 'secondary' : 'outline'}
      className="flex items-center justify-center gap-1"
    >
      {alignIcon === 'left' && (condition ? <MdiCheck /> : <MdiClose />)}
      {teamKey.substring(3)}
      {alignIcon === 'right' && (condition ? <MdiCheck /> : <MdiClose />)}
    </Badge>
  );
}

export function fmtFouls({
  foulCount,
  pointsPerFoul,
}: {
  foulCount: number | undefined;
  pointsPerFoul: number;
}): string {
  const definedFoulCount = foulCount ?? 0;

  return `${definedFoulCount} (+${definedFoulCount * pointsPerFoul})`;
}

export function FoulDisplay({
  foulsReceived,
  pointsPerFoul,
  techFoulsReceived,
  pointsPerTechFoul,
  techOrMajor,
}: {
  foulsReceived: number | undefined;
  pointsPerFoul: number;
  techFoulsReceived: number | undefined;
  pointsPerTechFoul: number;
  techOrMajor: 'tech' | 'major'; // 1992-2024 Tech; 2025+ Major
}) {
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="flex items-center gap-1">
        <span className="text-xs opacity-70">Regular:</span>
        <span>
          {fmtFouls({
            foulCount: foulsReceived,
            pointsPerFoul,
          })}
        </span>
      </div>
      <div className="flex items-center gap-1">
        <span className="text-xs opacity-70">
          {techOrMajor === 'tech' ? 'Tech' : 'Major'}:
        </span>
        <span>
          {fmtFouls({
            foulCount: techFoulsReceived,
            pointsPerFoul: pointsPerTechFoul,
          })}
        </span>
      </div>
    </div>
  );
}
