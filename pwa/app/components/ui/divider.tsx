import * as React from 'react';

import { cn } from '~/lib/utils';

const Divider = React.forwardRef<
  HTMLSpanElement,
  React.ComponentPropsWithoutRef<'span'>
>(({ className, children }, ref) => (
  <span className={cn('relative flex justify-center', className)} ref={ref}>
    <div
      className="absolute inset-x-0 top-1/2 h-px -translate-y-1/2 bg-transparent
        bg-gradient-to-r from-transparent via-gray-500 to-transparent
        opacity-75"
    ></div>

    <span className="relative z-10 bg-white px-6">{children}</span>
  </span>
));
Divider.displayName = 'Divider';

export { Divider };
