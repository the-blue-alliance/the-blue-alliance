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
}: {
  condition: boolean;
  teamKey: string;
}) {
  return (
    <Badge variant={condition ? 'success' : 'destructive'}>
      {teamKey.substring(3)}
    </Badge>
  );
}
