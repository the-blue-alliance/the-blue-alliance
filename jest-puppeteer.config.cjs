// Launch options for the browser that the jest-puppeteer preset provides as
// the global `browser`. The sandbox flags match what ops/tests/fullstack.test.js
// used when it launched puppeteer itself.
module.exports = {
  launch: {
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  },
};
