const { defineConfig, globalIgnores } = require("eslint/config");

const babelParser = require("@babel/eslint-parser");
const react = require("eslint-plugin-react");
const globals = require("globals");
const js = require("@eslint/js");

const { FlatCompat } = require("@eslint/eslintrc");

const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
});

module.exports = defineConfig([
  {
    languageOptions: {
      parser: babelParser,

      globals: {
        ...globals.jest,
        ...globals.jasmine,
        ...globals.browser,
        ...globals.jquery,
      },
    },

    extends: compat.extends("plugin:prettier/recommended"),

    plugins: {
      react,
    },

    rules: {
      "no-console": "warn",
    },
  },
  globalIgnores([
    "**/old_py2",
    "**/pwa/",
    "src/backend",
    "src/build",
    "**/subtrees",
    "**/venv/",
    "ops/dev/firebase",
  ]),
]);
