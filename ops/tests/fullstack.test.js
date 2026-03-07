import { setDefaultOptions } from "expect-puppeteer";
import puppeteer from "puppeteer";
import "regenerator-runtime/runtime";

jest.setTimeout(120000);
setDefaultOptions({ timeout: 120000 });

// Shared browser instance for all tests
let sharedBrowser;

beforeAll(async () => {
  sharedBrowser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
});

afterAll(async () => {
  if (sharedBrowser) await sharedBrowser.close();
});

describe("Homepage", () => {
  let page;

  beforeAll(async () => {
    page = await sharedBrowser.newPage();

    await page.goto("http://localhost:8080", {
      waitUntil: "networkidle2",
      timeout: 60000,
    });
    await page.waitForSelector(".navbar", { timeout: 30000 });
  });

  afterAll(async () => {
    if (page) await page.close();
  });

  it('should be titled "The Blue Alliance"', async () => {
    await expect(page.title()).resolves.toMatch("The Blue Alliance");
  });

  it("should render tagline", async () => {
    await expect(page).toMatchTextContent(
      "The Blue Alliance is the best way to scout"
    );
  });
});

describe("GameDay", () => {
  let page;

  beforeAll(async () => {
    page = await sharedBrowser.newPage();

    await page.goto("http://localhost:8080/gameday", {
      waitUntil: "networkidle2",
      timeout: 60000,
    });
    await page.waitForSelector(".gameday", { timeout: 30000 });
  });

  afterAll(async () => {
    if (page) await page.close();
  });

  it('should be titled "GameDay - The Blue Alliance"', async () => {
    await expect(page.title()).resolves.toMatch("GameDay - The Blue Alliance");
  });

  it('should render "Select a layout"', async () => {
    await expect(page).toMatchTextContent("Select a layout");
  });
});

describe("APIv3 Docs", () => {
  let page;

  beforeAll(async () => {
    page = await sharedBrowser.newPage();

    await page.goto("http://localhost:8080/apidocs/v3", {
      waitUntil: "networkidle2",
      timeout: 60000,
    });
    await page.waitForSelector("#swagger_url", { timeout: 30000 });
  });

  afterAll(async () => {
    if (page) await page.close();
  });

  it('should be titled "APIv3 - The Blue Alliance"', async () => {
    await expect(page.title()).resolves.toMatch("APIv3 - The Blue Alliance");
  });

  it("should render overview", async () => {
    await expect(page).toMatchTextContent(
      "Information and statistics about FIRST Robotics Competition teams and events."
    );
  });
});

describe("EventWizard2", () => {
  let page;

  beforeAll(async () => {
    page = await sharedBrowser.newPage();

    await page.goto("http://localhost:8080/eventwizard", {
      waitUntil: "networkidle2",
      timeout: 60000,
    });
    await page.waitForSelector("#eventwizard", { timeout: 30000 });
  });

  afterAll(async () => {
    if (page) await page.close();
  });

  it('should be titled "The Blue Alliance - EventWizard"', async () => {
    await expect(page.title()).resolves.toMatch(
      "The Blue Alliance - EventWizard"
    );
  });

  it('should render "Select Event"', async () => {
    await expect(page).toMatchTextContent("Select Event");
  });
});
