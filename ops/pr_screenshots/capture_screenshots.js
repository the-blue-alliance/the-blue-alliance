/* eslint-disable no-console */

const fs = require("fs");
const puppeteer = require("puppeteer");

const CAPTURE_URLS = [
  ["Homepage", "http://localhost:8080"],
  ["GameDay", "http://localhost:8080/gameday"],
];

async function main() {
  const executablePath =
    process.env.PUPPETEER_EXECUTABLE_PATH ||
    (fs.existsSync("/usr/bin/google-chrome")
      ? "/usr/bin/google-chrome"
      : undefined);

  const browser = await puppeteer.launch({
    headless: "new",
    ...(executablePath ? { executablePath } : {}),
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  try {
    const prNumber = process.env.GITHUB_PULL_REQUEST_NUMBER || "None";
    const results = [];
    const page = await browser.newPage();
    await page.setViewport({
      width: 1920,
      height: 1080,
      deviceScaleFactor: 1,
    });

    for (const [name, url] of CAPTURE_URLS) {
      console.error(`Screenshotting ${name}: ${url}`);
      try {
        await page.goto(url, { waitUntil: "networkidle2", timeout: 60000 });
        const buffer = await page.screenshot({ type: "png" });
        const image = buffer.toString("base64");
        const timestamp = Math.floor(Date.now() / 1000);
        const filename = `pr-${prNumber}-${url}-${timestamp}.png`
          .replace(/\//g, "-")
          .replace(/ /g, "");
        results.push([name, filename, image]);
      } catch (err) {
        console.error(`Error screenshotting ${name}: ${err}`);
      }
    }

    process.stdout.write(JSON.stringify(results));
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
