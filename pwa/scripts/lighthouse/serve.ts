import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import process from 'node:process';

const BUILD_ARTIFACT = 'build/server/server.js';

async function isUp(url: string): Promise<boolean> {
  try {
    const res = await fetch(url, { redirect: 'manual' });
    return res.status > 0;
  } catch {
    return false;
  }
}

async function waitUntilUp(url: string, timeoutMs: number): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await isUp(url)) return;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`Timed out waiting for ${url} after ${timeoutMs}ms`);
}

export interface ServeHandle {
  teardown: () => Promise<void>;
}

export async function serve(
  baseUrl: string,
  { autoServe }: { autoServe: boolean },
): Promise<ServeHandle> {
  const alreadyUp = await isUp(baseUrl);

  if (alreadyUp) {
    console.log(`↺ Reusing server already listening at ${baseUrl}`);
    return { teardown: async () => {} };
  }

  if (!autoServe) {
    throw new Error(`Nothing is serving ${baseUrl} and --no-server was set`);
  }

  if (!existsSync(BUILD_ARTIFACT)) {
    throw new Error(
      `Missing ${BUILD_ARTIFACT}. Run \`pnpm run build\` before collecting Lighthouse data.`,
    );
  }

  const port = new URL(baseUrl).port || '3000';
  console.log(`▶ Starting \`pnpm run start\` on port ${port}...`);

  const child = spawn('pnpm', ['run', 'start'], {
    env: { ...process.env, NODE_ENV: 'production', PORT: port },
    stdio: 'ignore',
    detached: true,
  });

  const teardown = async () => {
    if (child.pid !== undefined && !child.killed) {
      try {
        process.kill(-child.pid, 'SIGTERM');
      } catch {
        child.kill('SIGTERM');
      }
    }
  };

  try {
    await waitUntilUp(baseUrl, 120_000);
  } catch (error) {
    await teardown();
    throw error;
  }

  console.log(`✓ Server ready at ${baseUrl}`);
  return { teardown };
}
