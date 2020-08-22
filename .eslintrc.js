module.exports = {
  parser: "babel-eslint",
  extends: ["plugin:prettier/recommended"],
  plugins: ["react"],
  env: {
    jest: true,
    jasmine: true,
    browser: true,
    jquery: true,
  },
  rules: {
    "no-console": "warn",
  },
};
