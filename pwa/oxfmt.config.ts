import { defineConfig } from 'oxfmt';

export default defineConfig({
  semi: true,
  singleQuote: true,
  trailingComma: 'all',
  tabWidth: 2,
  printWidth: 80,
  sortImports: {
    newlinesBetween: true,
  },
  sortPackageJson: true,
  sortTailwindcss: {
    stylesheet: './app/tailwind.css',
    functions: ['clsx', 'cn', 'cva'],
  },
  ignorePatterns: ['app/routeTree.gen.ts', 'pnpm-lock.yaml'],
});
