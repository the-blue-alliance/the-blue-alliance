import React, { ReactNode } from 'react';

import { cn } from '~/lib/utils';

const TitledCard = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    cardTitle: ReactNode;
    cardSubtitle: ReactNode;
  }
>(({ cardTitle, cardSubtitle, className, ...props }, ref) => (
  <div
    className={cn(
      `flex flex-col justify-center rounded-lg border border-gray-100 px-4 py-6
      text-center transition-all duration-300 ease-in-out hover:-translate-y-1
      hover:border-gray-200 hover:shadow-md`,
      className,
    )}
    {...props}
    ref={ref}
  >
    <dd className="text-4xl font-extrabold">{cardTitle}</dd>
    <dt className="order-last text-lg font-medium text-gray-500">
      {cardSubtitle}
    </dt>
  </div>
));
TitledCard.displayName = 'TitledCard';

export { TitledCard };
