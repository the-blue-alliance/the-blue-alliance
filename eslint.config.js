const react = require("eslint-plugin-react");
const globals = require("globals");
const js = require("@eslint/js");

const { FlatCompat } = require("@eslint/eslintrc");

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
});

module.exports = [
  {
    ignores: [
      "**/old_py2",
      "**/pwa/",
      "src/backend",
      "src/build",
      "**/subtrees",
      "**/venv/",
      "ops/dev/firebase",
    ],
  },
  ...compat.extends("plugin:prettier/recommended"),
  {
    languageOptions: {
      parserOptions: {
        ecmaVersion: 2022,
        ecmaFeatures: {
          jsx: true,
        },
      },

      globals: {
        ...globals.jest,
        ...globals.jasmine,
        ...globals.browser,
        ...globals.jquery,
      },
    },

    plugins: {
      react,
    },

    rules: {
      "no-console": "warn",
    },
  },
];
