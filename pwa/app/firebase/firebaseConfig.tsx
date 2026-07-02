import { isServer } from '@tanstack/react-query';
import { initializeAnalytics } from 'firebase/analytics';
import { getApps, initializeApp } from 'firebase/app';
import { connectAuthEmulator, getAuth } from 'firebase/auth';
import { getDatabase } from 'firebase/database';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  databaseURL: import.meta.env.VITE_FIREBASE_DATABASE_URL,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
};

let app;
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

const database = getDatabase(app);
const analytics =
  !isServer && typeof window !== 'undefined'
    ? initializeAnalytics(app, { config: { send_page_view: false } })
    : null;
export { auth, analytics, database };
