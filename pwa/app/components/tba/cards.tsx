import React, { ReactNode } from 'react';

const TitledCard = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    cardTitle: ReactNode;
    cardSubtitle: ReactNode;
  }
>(({ cardTitle, cardSubtitle, ...props }, ref) => (
  <div
    className="flex flex-col rounded-lg border border-gray-100 px-4 py-8 text-center"
    {...props}
    ref={ref}
  >
    <dd className="text-4xl font-extrabold md:text-5xl">{cardTitle}</dd>
    <dt className="order-last text-lg font-medium text-gray-500">
      {cardSubtitle}
    </dt>
  </div>
));
TitledCard.displayName = 'TitledCard';

export { TitledCard };
