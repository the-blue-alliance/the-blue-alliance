import React, { ReactNode } from 'react';
import { cn } from '~/lib/utils';

interface InlineIconProps extends React.HTMLAttributes<HTMLDivElement> {
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
  ...props
}: InlineIconProps) {
  return (
    <div
      className={cn(
        'flex items-center text-center [&>*:first-child]:h-[1em] [&>*:first-child]:w-[1em]',
        className,
      )}
      {...props}
    >
      {children[0]}
      <span className="ml-1 block">{children.slice(1)}</span>
    </div>
  );
}
