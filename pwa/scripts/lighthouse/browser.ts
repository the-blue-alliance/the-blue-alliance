import { type Browser, chromium } from '@playwright/test';
import { createServer } from 'node:net';

function getFreePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.on('error', reject);
    server.listen(0, () => {
      const address = server.address();
      if (address === null || typeof address === 'string') {
        reject(new Error('Failed to acquire a free port'));
        return;
      }
      const { port } = address;
      server.close(() => resolve(port));
    });
  });
}

export interface BrowserHandle {
  port: number;
  close: () => Promise<void>;
}

export async function launchBrowser(): Promise<BrowserHandle> {
  const port = await getFreePort();
  const browser: Browser = await chromium.launch({
    headless: true,
    args: [`--remote-debugging-port=${port}`, '--no-sandbox'],
  });
  return { port, close: () => browser.close() };
}
