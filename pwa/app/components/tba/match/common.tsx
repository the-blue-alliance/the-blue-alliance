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
  teamKey?: string;
}) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          {condition ? <MdiCheck /> : <MdiClose />}
        </TooltipTrigger>
        <TooltipContent>{teamKey?.substring(3)}</TooltipContent>
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

/** Formats the fouls an alliance committed as "fouls / tech (or major) fouls". */
export function fmtFoulsCommitted({
  fouls,
  techFouls,
}: {
  fouls: number | undefined;
  techFouls: number | undefined;
}): string {
  return `${fouls ?? 0} / ${techFouls ?? 0}`;
}
