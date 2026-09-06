// End-to-end driver for the moderation API + PWA review UI.
// Drives headless Chrome against the local dev stack:
//   - TBA dev server (docker) on :8080 (web + api services, dispatch)
//   - PWA vite dev server on :5173
//   - Firebase auth emulator on :9099
// Captures screenshots into /tmp/moderation-evidence/ along the way.
//
// Usage: node scripts/moderation-e2e.mjs [stage...]
//   stages: seed, signin, grant, review, all (default)
import { chromium } from '@playwright/test';

const EVIDENCE_DIR = '/tmp/moderation-evidence';
const ADMIN_URL = 'http://localhost:8080/admin/suggestions/seed';
const PWA_URL = 'http://localhost:5173';
const MODERATOR_EMAIL = 'moderator@example.com';

const TYPES = [
  'match',
  'media',
  'social-media',
  'robot',
  'event_media',
  'event',
  'offseason-event',
  'api_auth_access',
];

let shotIndex = 0;
async function shot(page, name) {
  shotIndex += 1;
  const path = `${EVIDENCE_DIR}/${String(shotIndex).padStart(2, '0')}-${name}.png`;
  await page.screenshot({ path, fullPage: true });
  console.log(`  📸 ${path}`);
}

async function adminLogin(page) {
  await page.goto(ADMIN_URL);
  if (
    page.url().includes('_ah/login') ||
    (await page.locator('#submit-login').count()) > 0
  ) {
    await page.fill('#email', 'admin@example.com');
    await page.check('#admin');
    await page.click('#submit-login');
    await page.waitForURL('**/admin/suggestions/seed');
  }
}

async function seedSuggestions(page, { grantEmail, rounds = 1 } = {}) {
  console.log('STAGE: seed');
  await adminLogin(page);
  await shot(page, 'admin-seed-page');
  for (let i = 0; i < rounds; i++) {
    if (grantEmail) {
      await page.fill('#grant_email', grantEmail);
    }
    await page.click('button[type="submit"]');
    await page.waitForSelector('.alert-info');
  }
  await shot(page, 'admin-seed-results');
  const results = await page.locator('.alert-info li').allTextContents();
  console.log('  seed results:', results.join(' | '));
}

const FIREBASE_API_KEY = 'fake-api-key';
const AUTH_EMULATOR = 'http://localhost:9099';

// Sign in via the auth emulator's REST API and inject the resulting session
// into Firebase's IndexedDB persistence. signInWithPopup stopped opening
// popups under headless Chrome with newer firebase-js-sdk versions, so the
// widget flow can't be driven; this is equivalent and faster.
export async function emulatorSignIn(context) {
  const fakeIdToken = JSON.stringify({
    sub: 'headless-moderator',
    email: MODERATOR_EMAIL,
    email_verified: true,
  });
  const resp = await fetch(
    `${AUTH_EMULATOR}/identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key=${FIREBASE_API_KEY}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        postBody: `id_token=${encodeURIComponent(fakeIdToken)}&providerId=google.com`,
        requestUri: 'http://localhost',
        returnSecureToken: true,
      }),
    },
  );
  const tokens = await resp.json();
  if (!tokens.idToken) {
    throw new Error(`Emulator sign-in failed: ${JSON.stringify(tokens)}`);
  }
  const authUser = {
    uid: tokens.localId,
    email: tokens.email,
    emailVerified: true,
    displayName: 'Test Moderator',
    isAnonymous: false,
    providerData: [
      {
        providerId: 'google.com',
        uid: 'headless-moderator',
        displayName: 'Test Moderator',
        email: tokens.email,
        phoneNumber: null,
        photoURL: null,
      },
    ],
    stsTokenManager: {
      refreshToken: tokens.refreshToken,
      accessToken: tokens.idToken,
      expirationTime: Date.now() + Number(tokens.expiresIn ?? 3600) * 1000,
    },
    createdAt: String(Date.now()),
    lastLoginAt: String(Date.now()),
    apiKey: FIREBASE_API_KEY,
    appName: '[DEFAULT]',
  };
  await context.addInitScript(
    ({ user, apiKey }) => {
      const request = indexedDB.open('firebaseLocalStorageDb', 1);
      request.onupgradeneeded = () => {
        request.result.createObjectStore('firebaseLocalStorage', {
          keyPath: 'fbase_key',
        });
      };
      request.onsuccess = () => {
        const tx = request.result.transaction(
          'firebaseLocalStorage',
          'readwrite',
        );
        tx.objectStore('firebaseLocalStorage').put({
          fbase_key: `firebase:authUser:${apiKey}:[DEFAULT]`,
          value: user,
        });
      };
    },
    { user: authUser, apiKey: FIREBASE_API_KEY },
  );
}

async function signInToPwa(page, context) {
  console.log('STAGE: signin');
  await emulatorSignIn(context);
  await page.goto(`${PWA_URL}/suggest/review`);
  await page.waitForLoadState('networkidle');
  // The injected session may land after Firebase's first persistence read
  // on a cold load; a reload always picks it up
  if (
    (await page.getByRole('button', { name: /sign in with google/i }).count()) >
    0
  ) {
    await page.reload();
    await page.waitForLoadState('networkidle');
  }
  await page.waitForTimeout(1500);
  await shot(page, 'pwa-after-signin');
}

async function reviewType(page, type, index) {
  console.log(`STAGE: review ${type}`);
  await page.goto(`${PWA_URL}/suggest/review/${type}`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
  await shot(page, `review-${type}-queue`);

  const cards = page.locator('[data-testid^="suggestion-"]');
  const count = await cards.count();
  console.log(`  ${count} pending suggestions`);
  if (count === 0) {
    console.log(`  ⚠️ nothing to review for ${type}`);
    return { type, accepted: false, reason: 'empty queue' };
  }

  let expectedRemaining = 0;
  if (type === 'offseason-event') {
    // Offseason events require a unique event short code to accept, so
    // review just the first card individually. Event shorts must be
    // letters then at most 3 digits (Event.validate_key_name).
    const shortInput = page.getByLabel(/event short/i).first();
    await shortInput.fill(`test${Date.now() % 1000}`);
    await cards.first().getByRole('button', { name: '(a)ccept' }).click();
    expectedRemaining = count - 1;
  } else {
    // Bulk flow: select all accepts, then submit
    await page.getByRole('button', { name: 'Select All Accepts' }).click();
  }
  await shot(page, `review-${type}-selected`);
  await page.getByTestId('submit-review').click();
  await page.waitForTimeout(1500);

  // Accepts are transactional but the queue re-query is eventually
  // consistent on the dev datastore; poll until the list settles.
  let remaining = await page.locator('[data-testid^="suggestion-"]').count();
  for (
    let attempt = 0;
    attempt < 10 && remaining > expectedRemaining;
    attempt++
  ) {
    await page.waitForTimeout(2000);
    await page.goto(`${PWA_URL}/suggest/review/${type}`);
    await page.waitForLoadState('networkidle');
    remaining = await page.locator('[data-testid^="suggestion-"]').count();
  }
  await shot(page, `review-${type}-after-accept`);

  const emptyVisible = await page.getByText(/queue is empty/i).count();
  console.log(`  remaining: ${remaining}, empty message: ${emptyVisible > 0}`);
  return { type, accepted: remaining < count };
}

async function main() {
  const stages = process.argv.slice(2);
  const run = (stage) =>
    stages.length === 0 || stages.includes('all') || stages.includes(stage);

  // channel: 'chromium' forces the full Chromium build in (new) headless
  // mode, avoiding the separate headless-shell download
  const browser = await chromium.launch({ channel: 'chromium' });
  const adminContext = await browser.newContext({
    viewport: { width: 1280, height: 1024 },
  });
  const pwaContext = await browser.newContext({
    viewport: { width: 1280, height: 1024 },
  });
  const adminPage = await adminContext.newPage();
  const pwaPage = await pwaContext.newPage();
  pwaPage.on('console', (msg) => {
    if (msg.type() === 'error') console.log(`  [browser error] ${msg.text()}`);
  });

  const summary = [];
  try {
    if (run('seed')) {
      await seedSuggestions(adminPage, { rounds: 2 });
    }
    if (run('signin')) {
      await signInToPwa(pwaPage, pwaContext);
    }
    if (run('grant')) {
      console.log('STAGE: grant permissions');
      await seedSuggestions(adminPage, {
        grantEmail: MODERATOR_EMAIL,
        rounds: 1,
      });
      // Wait out datastore eventual consistency on the permission grant
      for (let attempt = 0; attempt < 6; attempt++) {
        await pwaPage.goto(`${PWA_URL}/suggest/review`);
        await pwaPage.waitForLoadState('networkidle');
        await pwaPage.waitForTimeout(1500);
        if ((await pwaPage.getByTestId('count-match').count()) > 0) break;
        console.log('  permissions not visible yet, retrying...');
        await pwaPage.waitForTimeout(2000);
      }
      await shot(pwaPage, 'pwa-review-dashboard');
    }
    if (run('review')) {
      for (let i = 0; i < TYPES.length; i++) {
        summary.push(await reviewType(pwaPage, TYPES[i], i));
      }
      await pwaPage.goto(`${PWA_URL}/suggest/review`);
      await pwaPage.waitForLoadState('networkidle');
      await pwaPage.waitForTimeout(1500);
      await shot(pwaPage, 'pwa-review-dashboard-final');
    }
    console.log('\nSUMMARY:');
    for (const result of summary) {
      console.log(
        `  ${result.accepted ? '✅' : '❌'} ${result.type}${result.reason ? ` (${result.reason})` : ''}`,
      );
    }
  } catch (error) {
    console.error('E2E FAILED:', error.message);
    await shot(pwaPage, 'FAILURE-pwa');
    await shot(adminPage, 'FAILURE-admin');
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

// Only run when executed directly, so emulatorSignIn stays importable
if (import.meta.url === `file://${process.argv[1]}`) {
  await main();
}
