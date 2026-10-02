import { createFileRoute, redirect } from '@tanstack/react-router';

export const Route = createFileRoute('/gameday/$eventCode')({
  beforeLoad: ({ params: { eventCode } }) => {
    throw redirect({
      to: '/gameday',
      search: { event: eventCode },
    });
  },
}); // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop
