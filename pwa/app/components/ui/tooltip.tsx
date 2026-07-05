import { Tooltip as TooltipPrimitive } from '@base-ui/react/tooltip';
import { type ComponentProps } from 'react';

import { cn } from '~/lib/utils';

function TooltipProvider({
  delay = 0,
  ...props
}: ComponentProps<typeof TooltipPrimitive.Provider>) {
  return (
    <TooltipPrimitive.Provider
      data-slot="tooltip-provider"
      delay={delay}
      {...props}
    />
  );
}

function Tooltip({ ...props }: ComponentProps<typeof TooltipPrimitive.Root>) {
  return <TooltipPrimitive.Root data-slot="tooltip" {...props} />;
}

function TooltipTrigger({
  ...props
}: ComponentProps<typeof TooltipPrimitive.Trigger>) {
  return <TooltipPrimitive.Trigger data-slot="tooltip-trigger" {...props} />;
}

function TooltipContent({
  className,
  side,
  sideOffset = 0,
  align,
  alignOffset,
  children,
  ...props
}: ComponentProps<typeof TooltipPrimitive.Popup> &
  Pick<
    ComponentProps<typeof TooltipPrimitive.Positioner>,
    'side' | 'sideOffset' | 'align' | 'alignOffset'
  >) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Positioner
        side={side}
        sideOffset={sideOffset}
        align={align}
        alignOffset={alignOffset}
        className="isolate z-50"
      >
        <TooltipPrimitive.Popup
          data-slot="tooltip-content"
          className={cn(
            `z-50 w-fit max-w-xs origin-(--transform-origin) animate-in
            rounded-md border bg-popover text-xs text-popover-foreground
            fade-in-0 zoom-in-95 data-[side=bottom]:slide-in-from-top-2
            data-[side=left]:slide-in-from-right-2
            data-[side=right]:slide-in-from-left-2
            data-[side=top]:slide-in-from-bottom-2 data-closed:animate-out
            data-closed:fade-out-0 data-closed:zoom-out-95`,
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
        </TooltipPrimitive.Popup>
      </TooltipPrimitive.Positioner>
    </TooltipPrimitive.Portal>
  );
}

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider };
