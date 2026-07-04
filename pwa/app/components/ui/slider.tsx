import { Slider as SliderPrimitive } from '@base-ui/react/slider';

import { cn } from '~/lib/utils';

function Slider({ className, ...props }: SliderPrimitive.Root.Props) {
  return (
    <SliderPrimitive.Root
      thumbAlignment="edge"
      className={cn(
        'relative flex w-full touch-none items-center select-none',
        className,
      )}
      {...props}
    >
      <SliderPrimitive.Control
        className="relative flex w-full touch-none items-center select-none"
      >
        <SliderPrimitive.Track
          className="relative h-2 w-full grow overflow-hidden rounded-full
            bg-secondary"
        >
          <SliderPrimitive.Indicator className="absolute h-full bg-primary" />
        </SliderPrimitive.Track>
        <SliderPrimitive.Thumb
          className="block h-5 w-5 rounded-full border-2 border-primary
            bg-background ring-offset-background transition-colors
            focus-visible:ring-2 focus-visible:ring-ring
            focus-visible:ring-offset-2 focus-visible:outline-none
            disabled:pointer-events-none disabled:opacity-50"
        />
      </SliderPrimitive.Control>
    </SliderPrimitive.Root>
  );
}

export { Slider };
