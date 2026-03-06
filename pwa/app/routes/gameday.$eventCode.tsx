import { createFileRoute, redirect } from '@tanstack/react-router';

export const Route = createFileRoute('/gameday/$eventCode')({
  beforeLoad: ({ params: { eventCode } }) => {
    throw redirect({
      to: '/gameday',
      search: { event: eventCode },
    });
  },
});
