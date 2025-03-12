import { VariantProps, cva } from 'class-variance-authority';
import React, { ReactNode } from 'react';

import { cn } from '~/lib/utils';

// For very long text blocks, flex makes the icon really tiny. Use flexless for those.
// Flex approach in general is easier to work with, so that's the default.
const inlineIconVariants = cva('', {
  variants: {
    displayStyle: {
      flex: 'flex items-center text-center',
      flexless: '*:inline',
    },
    iconSize: {
      default: '[&>*:first-child]:size-[1em]',
      large: '[&>*:first-child]:size-[1.5em]',
    },
  },
  defaultVariants: {
    displayStyle: 'flex',
    iconSize: 'default',
  },
});

interface InlineIconProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof inlineIconVariants> {
  children: ReactNode[];
}
/**
 * Helper component to put an SVG icon nicely inline with text. The first child of this component
 * should be the SVG icon. Example usage:
 *
 * <InlineIcon>
 *    <MySvg />
 *    This is my inline text!
 * </InlineIcon>
 */
export default function InlineIcon({
  className,
  children,
  displayStyle,
  iconSize,
  ...props
}: InlineIconProps) {
  return (
    <div
      className={cn(inlineIconVariants({ displayStyle, iconSize, className }))}
      {...props}
    >
      {children[0]}
      <span className="ml-1">{children.slice(1)}</span>
    </div>
  );
}
