import { createFileRoute, notFound, redirect } from '@tanstack/react-router';

import { resolveShortKey } from '~/lib/shortUrl';

export const Route = createFileRoute('/$shortKey')({
  beforeLoad: ({ params: { shortKey } }) => {
    const target = resolveShortKey(shortKey);
    if (target === null) {
      throw notFound();
    }

    switch (target.type) {
      case 'team':
        throw redirect({
          to: '/team/$teamNumber/{-$year}',
          params: { teamNumber: target.teamNumber },
          statusCode: 301,
        });
      case 'district':
        throw redirect({
          to: '/district/$districtAbbreviation/{-$year}',
          params: {
            districtAbbreviation: target.abbreviation,
            year: target.year,
          },
          statusCode: 301,
        });
      case 'event':
        throw redirect({
          to: '/event/$eventKey',
          params: { eventKey: target.eventKey },
          statusCode: 301,
        });
    }
  },
}); // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop
