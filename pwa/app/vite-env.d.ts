/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_TBA_API_READ_KEY: string;
  readonly VITE_FIREBASE_API_KEY: string;
  readonly VITE_FIREBASE_AUTH_DOMAIN: string;
  readonly VITE_FIREBASE_PROJECT_ID: string;
  readonly VITE_SESSION_SECRET: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare global {
  namespace NodeJS {
    interface ProcessEnv {
      readonly FIREBASE_PROJECT_ID: string;
      readonly FIREBASE_CLIENT_EMAIL: string;
      readonly FIREBASE_PRIVATE_KEY: string;
    }
  }
}
