import * as Sentry from '@sentry/tanstackstart-react';
import compression from 'compression';
import express from 'express';
import morgan from 'morgan';
import { toNodeHandler } from 'srvx/node';

const isProd = process.env.NODE_ENV === 'production';
if (!isProd) {
  throw new Error('This server should only be run in production mode');
}

Sentry.init({
  dsn: 'https://1420d805bff3f6f12a13817725266abd@o4507688293695488.ingest.us.sentry.io/4507745278492672',
  sendDefaultPii: false,
  enableLogs: true,
  enableMetrics: true,
  tracesSampleRate: 1.0,
});

const app = express();

app.use(compression());

// http://expressjs.com/en/advanced/best-practice-security.html#at-a-minimum-disable-x-powered-by-header
app.disable('x-powered-by');

// Vite fingerprints its assets so we can cache forever.
app.use(
  '/assets',
  express.static('build/client/assets', { immutable: true, maxAge: '1y' }),
);

// Cache favicon for 1 week.
app.use(
  '/favicon.ico',
  express.static('build/client/favicon.ico', { maxAge: '1w' }),
);

// Everything else is cached for 24 hours.
app.use(express.static('build/client', { maxAge: '24h' }));

app.use(morgan('tiny'));

// handle SSR requests
const { default: handler } = await import('./build/server/server.js');
const nodeHandler = toNodeHandler(handler.fetch);
app.use(async (req, res, next) => {
  // Enable JavaScript profiling for Sentry browser profiling
  res.setHeader('Document-Policy', 'js-profiling');

  try {
    await nodeHandler(req, res);
  } catch (error) {
    next(error);
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () =>
  console.log(`Express server listening at http://localhost:${port}`),
);
