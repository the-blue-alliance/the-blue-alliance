import MdiCheck from '~icons/mdi/check';
import MdiClose from '~icons/mdi/close';

import { Badge } from '~/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';

function ConditionIcon({ condition }: { condition: boolean }) {
  return condition ? (
    <MdiCheck role="img" aria-label="Achieved" />
  ) : (
    <MdiClose role="img" aria-label="Not achieved" />
  );
}

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
          <ConditionIcon condition={condition} />
        </TooltipTrigger>
        <TooltipContent>{teamKey.substring(3)}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export function ConditionalRpAchieved({ condition }: { condition: boolean }) {
  return (
    <div className="flex items-center justify-center">
      <ConditionIcon condition={condition} />
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
      {alignIcon === 'left' && <ConditionIcon condition={condition} />}
      {teamKey.substring(3)}
      {alignIcon === 'right' && <ConditionIcon condition={condition} />}
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
