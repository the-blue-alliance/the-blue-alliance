export default {
  semi: true,
  singleQuote: true,
  trailingComma: 'all',
  tabWidth: 2,
  plugins: [
    'prettier-plugin-tailwindcss',
    'prettier-plugin-classnames',
    '@trivago/prettier-plugin-sort-imports',
  ],
  tailwindFunctions: ['clsx', 'cn'],
  customFunctions: ['clsx', 'cn'],
  importOrder: ['^@/(.*)$', '^~/(.*)$', '^[./]'],
  importOrderSeparation: true,
  importOrderSortSpecifiers: true,
};
