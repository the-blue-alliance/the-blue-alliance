import { createFileRoute, redirect } from '@tanstack/react-router';

const BIGQUERY_URL =
  'https://console.cloud.google.com/bigquery?project=tbatv-prod-hrd&p=tbatv-prod-hrd&d=the_blue_alliance&page=dataset';

export const Route = createFileRoute('/bigquery')({
  beforeLoad: () => {
    throw redirect({ href: BIGQUERY_URL, statusCode: 302 });
  },
}); // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop
