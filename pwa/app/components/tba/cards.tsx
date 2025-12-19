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
      `flex flex-col justify-center rounded-lg border border-border px-4 py-6
      text-center transition-all duration-300 ease-in-out hover:-translate-y-1
      hover:border-border hover:shadow-md`,
      className,
    )}
    {...props}
    ref={ref}
  >
    <dd className="text-4xl font-extrabold">{cardTitle}</dd>
    <dt className="order-last text-lg font-medium text-muted-foreground">
      {cardSubtitle}
    </dt>
  </div>
));
TitledCard.displayName = 'TitledCard';

export { TitledCard };
