import { createFileRoute, redirect } from '@tanstack/react-router';

export const Route = createFileRoute('/events/$districtAbbrev_/$year')({
  beforeLoad: ({ params: { districtAbbrev, year } }) => {
    throw redirect({
      to: `/district/${districtAbbrev}/${year}`,
    });
  },
});
