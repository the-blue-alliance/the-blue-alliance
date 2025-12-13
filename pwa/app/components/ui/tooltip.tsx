import * as TooltipPrimitive from '@radix-ui/react-tooltip';
import * as React from 'react';

import { cn } from '~/lib/utils';

function TooltipProvider({
  delayDuration = 0,
  ...props
}: React.ComponentProps<typeof TooltipPrimitive.Provider>) {
  return (
    <TooltipPrimitive.Provider
      data-slot="tooltip-provider"
      delayDuration={delayDuration}
      {...props}
    />
  );
}

function Tooltip({
  ...props
}: React.ComponentProps<typeof TooltipPrimitive.Root>) {
  return (
    <TooltipProvider>
      <TooltipPrimitive.Root data-slot="tooltip" {...props} />
    </TooltipProvider>
  );
}

function TooltipTrigger({
  ...props
}: React.ComponentProps<typeof TooltipPrimitive.Trigger>) {
  return <TooltipPrimitive.Trigger data-slot="tooltip-trigger" {...props} />;
}

function TooltipContent({
  className,
  sideOffset = 0,
  children,
  ...props
}: React.ComponentProps<typeof TooltipPrimitive.Content>) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Content
        data-slot="tooltip-content"
        sideOffset={sideOffset}
        className={cn(
          `z-50 w-fit max-w-xs origin-(--radix-tooltip-content-transform-origin)
          animate-in rounded-md border bg-popover text-xs
          text-popover-foreground fade-in-0 zoom-in-95
          data-[side=bottom]:slide-in-from-top-2
          data-[side=left]:slide-in-from-right-2
          data-[side=right]:slide-in-from-left-2
          data-[side=top]:slide-in-from-bottom-2 data-[state=closed]:animate-out
          data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95`,
          className,
        )}
        style={{
          filter:
            'drop-shadow(0 10px 8px rgb(0 0 0 / 0.04)) drop-shadow(0 4px 3px rgb(0 0 0 / 0.1))',
        }}
        {...props}
      >
        <div
          className="relative z-10 max-h-60 overflow-x-hidden overflow-y-auto
            px-3 py-1.5 text-center text-balance [&::-webkit-scrollbar]:w-2
            [&::-webkit-scrollbar-thumb]:rounded-full
            [&::-webkit-scrollbar-thumb]:bg-muted-foreground/30
            [&::-webkit-scrollbar-track]:bg-transparent"
        >
          {children}
        </div>
        <TooltipPrimitive.Arrow
          className="relative -z-10 size-3 translate-y-[calc(-50%_-_2px)]
            rotate-45 rounded-[2px] bg-popover fill-popover"
        />
      </TooltipPrimitive.Content>
    </TooltipPrimitive.Portal>
  );
}

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider };
