import { createFileRoute, redirect } from '@tanstack/react-router';

export const Route = createFileRoute('/events/$districtAbbreviation/$year')({
  beforeLoad: ({ params: { districtAbbreviation, year } }) => {
    throw redirect({
      to: '/district/$districtAbbreviation/{-$year}',
      params: { districtAbbreviation, year },
    });
  },
}); // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop
