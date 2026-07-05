import { Checkbox as CheckboxPrimitive } from '@base-ui/react/checkbox';

import CheckIcon from '~icons/lucide/check';

import { cn } from '~/lib/utils';

function Checkbox({ className, ...props }: CheckboxPrimitive.Root.Props) {
  return (
    <CheckboxPrimitive.Root
      className={cn(
        `peer grid h-4 w-4 shrink-0 place-content-center rounded-sm border
        border-primary ring-offset-background focus-visible:ring-2
        focus-visible:ring-ring focus-visible:ring-offset-2
        focus-visible:outline-none disabled:cursor-not-allowed
        disabled:opacity-50 data-checked:bg-primary
        data-checked:text-primary-foreground`,
        className,
      )}
      {...props}
    >
      <CheckboxPrimitive.Indicator
        className={cn('grid place-content-center text-current')}
      >
        <CheckIcon className="h-4 w-4" />
      </CheckboxPrimitive.Indicator>
    </CheckboxPrimitive.Root>
  );
}

export { Checkbox };
