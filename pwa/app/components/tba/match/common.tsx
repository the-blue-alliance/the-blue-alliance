import MdiCheck from '~icons/mdi/check';
import MdiClose from '~icons/mdi/close';

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
