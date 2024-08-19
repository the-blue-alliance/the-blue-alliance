/**
 * By default, Remix will handle hydrating your app on the client for you.
 * You are free to delete this file if you'd like to, but if you ever want it revealed again, you can run `npx remix reveal` ✨
 * For more information, see https://remix.run/file-conventions/entry.client
 */
import { RemixBrowser, useLocation, useMatches } from '@remix-run/react';
import * as Sentry from '@sentry/remix';
import { StrictMode, startTransition, useEffect } from 'react';
import { hydrateRoot } from 'react-dom/client';

Sentry.init({
  dsn: 'https://1420d805bff3f6f12a13817725266abd@o4507688293695488.ingest.us.sentry.io/4507745278492672',
  tracePropagationTargets: [/^https:\/\/beta\.thebluealliance\.com/],
  tracesSampleRate: 1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1,

  integrations: [
    Sentry.browserTracingIntegration({
      useEffect,
      useLocation,
      useMatches,
    }),
    // https://github.com/getsentry/sentry-javascript/issues/12706
    // eslint-disable-next-line import/namespace
    Sentry.replayIntegration(),
  ],
  enabled: process.env.NODE_ENV === 'production',
});

startTransition(() => {
  hydrateRoot(
    document,
    <StrictMode>
      <RemixBrowser />
    </StrictMode>,
  );
});
