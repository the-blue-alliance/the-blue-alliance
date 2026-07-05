import { Button as ButtonPrimitive } from '@base-ui/react/button';
import { type VariantProps, cva } from 'class-variance-authority';

import { cn } from '~/lib/utils';

const buttonVariants = cva(
  `inline-flex cursor-pointer items-center justify-center rounded-md text-sm
  font-medium whitespace-nowrap ring-offset-background transition-colors
  focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2
  focus-visible:outline-hidden disabled:pointer-events-none disabled:opacity-50`,
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive:
          'text-destructive-foreground bg-destructive hover:bg-destructive/90',
        outline: `border border-input bg-background hover:bg-accent
        hover:text-accent-foreground`,
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
        success: 'bg-green-600 text-white hover:bg-green-700',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'size-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

export interface ButtonProps
  extends ButtonPrimitive.Props, VariantProps<typeof buttonVariants> {}

function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <ButtonPrimitive
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };
