import * as Sentry from '@sentry/remix';

Sentry.init({
  dsn: 'https://1420d805bff3f6f12a13817725266abd@o4507688293695488.ingest.us.sentry.io/4507745278492672',
  tracesSampleRate: 1,
  autoInstrumentRemix: true,
});
