import { type HTMLAttributes, type ReactNode, forwardRef } from 'react';

import { cn } from '~/lib/utils';

const TitledCard = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement> & {
    cardTitle: ReactNode;
    cardSubtitle: ReactNode;
  }
>(({ cardTitle, cardSubtitle, className, ...props }, ref) => (
  <div
    className={cn(
      `flex flex-col justify-center overflow-hidden rounded-lg border
      border-border/50 bg-gradient-to-br from-muted/30 to-muted/10 px-6 py-8
      text-center shadow-sm transition-all duration-300 ease-in-out
      hover:-translate-y-1 hover:shadow-md`,
      className,
    )}
    {...props}
    ref={ref}
  >
    <dd className="text-4xl leading-tight font-extrabold tracking-tight">
      {cardTitle}
    </dd>
    <dt
      className="order-last mt-3 text-base font-semibold text-muted-foreground"
    >
      {cardSubtitle}
    </dt>
  </div>
));
TitledCard.displayName = 'TitledCard';

export { TitledCard };
