import * as SliderPrimitive from '@radix-ui/react-slider';
import React, { useState } from 'react';

import { cn } from '~/lib/utils';

type SliderProps = {
  className?: string;
  min: number;
  max: number;
  minStepsBetweenThumbs: number;
  step: number;
  formatLabel?: (value: number) => string;
  value?: number[] | readonly number[];
  onValueChange?: (values: number[]) => void;
};

const DoubleSlider = React.forwardRef(
  (
    {
      className,
      min,
      max,
      step,
      formatLabel,
      value,
      onValueChange,
      ...props
    }: SliderProps,
    ref,
  ) => {
    const initialValue = Array.isArray(value) ? value : [min, max];
    const [localValues, setLocalValues] = useState(initialValue);

    const handleValueChange = (newValues: number[]) => {
      setLocalValues(newValues);
      if (onValueChange) {
        onValueChange(newValues);
      }
    };

    return (
      <SliderPrimitive.Root
        ref={ref as React.RefObject<HTMLDivElement>}
        min={min}
        max={max}
        step={step}
        value={localValues}
        onValueChange={handleValueChange}
        className={cn(
          'relative mb-6 flex w-full touch-none items-center select-none',
          className,
        )}
        {...props}
      >
        <SliderPrimitive.Track
          className="relative h-1.5 w-full grow overflow-hidden rounded-full
            bg-primary/20"
        >
          <SliderPrimitive.Range className="absolute h-full bg-primary" />
        </SliderPrimitive.Track>
        {localValues.map((value, index) => (
          <SliderPrimitive.Thumb
            key={index}
            className="block h-4 w-4 rounded-full border border-primary/50
              bg-background shadow transition-colors focus-visible:ring-1
              focus-visible:ring-ring focus-visible:outline-none
              disabled:pointer-events-none disabled:opacity-50"
          />
        ))}
        <div className="absolute top-4 left-0">
          <span className="text-sm">
            {formatLabel
              ? formatLabel(Math.min(...localValues))
              : Math.min(...localValues)}
          </span>
        </div>
        <div className="absolute top-4 right-0">
          <span className="text-sm">
            {formatLabel
              ? formatLabel(Math.max(...localValues))
              : Math.max(...localValues)}
          </span>
        </div>
      </SliderPrimitive.Root>
    );
  },
);

DoubleSlider.displayName = 'DoubleSlider';

export { DoubleSlider };
