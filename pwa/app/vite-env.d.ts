/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_TBA_API_READ_KEY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
