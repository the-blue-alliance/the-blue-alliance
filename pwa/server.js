import { createRequestHandler } from '@react-router/express';
import { nodeProfilingIntegration } from '@sentry/profiling-node';
import * as Sentry from '@sentry/react-router';
import compression from 'compression';
import express from 'express';
import morgan from 'morgan';

const isProd = process.env.NODE_ENV === 'production';

Sentry.init({
  dsn: 'https://1420d805bff3f6f12a13817725266abd@o4507688293695488.ingest.us.sentry.io/4507745278492672',
  tracesSampleRate: 1,
  autoInstrumentRemix: true,
  enabled: isProd,
  integrations: [nodeProfilingIntegration()],
  profilesSampleRate: 1.0,
});

const viteDevServer = isProd
  ? undefined
  : await import('vite').then((vite) =>
      vite.createServer({
        server: { middlewareMode: true },
      }),
    );

const remixHandler = createRequestHandler({
  build: viteDevServer
    ? () => viteDevServer.ssrLoadModule('virtual:react-router/server-build')
    : // Ignore the eslint error since the ./build directory doesn't exist until the build script is run.
      // eslint-disable-next-line import/no-unresolved
      await import('./build/server/index.js'),
});

const app = express();

app.use(compression());

// http://expressjs.com/en/advanced/best-practice-security.html#at-a-minimum-disable-x-powered-by-header
app.disable('x-powered-by');

// handle asset requests
if (viteDevServer) {
  app.use(viteDevServer.middlewares);
} else {
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
}

app.use(morgan('tiny'));

// handle SSR requests
app.all('*', remixHandler);

const port = process.env.PORT || (isProd ? 3000 : 5173);
app.listen(port, () =>
  console.log(`Express server listening at http://localhost:${port}`),
);
