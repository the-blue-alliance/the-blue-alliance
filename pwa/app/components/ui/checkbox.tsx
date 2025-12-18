import * as CheckboxPrimitive from '@radix-ui/react-checkbox';
import { Check } from 'lucide-react';
import {
  type ComponentPropsWithoutRef,
  type ElementRef,
  forwardRef,
} from 'react';

import { cn } from '~/lib/utils';

const Checkbox = forwardRef<
  ElementRef<typeof CheckboxPrimitive.Root>,
  ComponentPropsWithoutRef<typeof CheckboxPrimitive.Root>
>(({ className, ...props }, ref) => (
  <CheckboxPrimitive.Root
    ref={ref}
    className={cn(
      `peer grid h-4 w-4 shrink-0 place-content-center rounded-sm border
      border-primary ring-offset-background focus-visible:ring-2
      focus-visible:ring-ring focus-visible:ring-offset-2
      focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50
      data-[state=checked]:bg-primary
      data-[state=checked]:text-primary-foreground`,
      className,
    )}
    {...props}
  >
    <CheckboxPrimitive.Indicator
      className={cn('grid place-content-center text-current')}
    >
      <Check className="h-4 w-4" />
    </CheckboxPrimitive.Indicator>
  </CheckboxPrimitive.Root>
));
Checkbox.displayName = CheckboxPrimitive.Root.displayName;

export { Checkbox };
