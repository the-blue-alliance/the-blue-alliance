/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_TBA_API_READ_KEY: string;
  readonly VITE_FIREBASE_API_KEY: string;
  readonly VITE_FIREBASE_AUTH_DOMAIN: string;
  readonly VITE_FIREBASE_PROJECT_ID: string;
  readonly VITE_FIREBASE_DATABASE_URL: string;
  readonly VITE_FIREBASE_AUTH_EMULATOR_HOST?: string;
  readonly VITE_TBA_MOBILE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
