import { isServer } from '@tanstack/react-query';
import type { Analytics } from 'firebase/analytics';
import { type FirebaseApp, getApps, initializeApp } from 'firebase/app';
import { connectAuthEmulator, getAuth } from 'firebase/auth';
import type { Database } from 'firebase/database';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  databaseURL: import.meta.env.VITE_FIREBASE_DATABASE_URL,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
};

let app: FirebaseApp;
if (!getApps().length) {
  app = initializeApp(firebaseConfig);
} else {
  app = getApps()[0];
}

const auth = isServer ? null : getAuth(app);

if (auth && import.meta.env.VITE_FIREBASE_AUTH_EMULATOR_HOST) {
  connectAuthEmulator(auth, import.meta.env.VITE_FIREBASE_AUTH_EMULATOR_HOST, {
    disableWarnings: true,
  });
}

let cachedDatabase: Database | null = null;
export async function getDatabaseInstance(): Promise<Database> {
  if (cachedDatabase) return cachedDatabase;
  const { getDatabase } = await import('firebase/database');
  cachedDatabase = getDatabase(app);
  return cachedDatabase;
}

let cachedAnalytics: Analytics | null = null;
export async function getAnalyticsInstance(): Promise<Analytics | null> {
  if (isServer || typeof window === 'undefined') return null;
  if (cachedAnalytics) return cachedAnalytics;
  const { initializeAnalytics } = await import('firebase/analytics');
  cachedAnalytics = initializeAnalytics(app, {
    config: { send_page_view: false },
  });
  return cachedAnalytics;
}

export { auth };
