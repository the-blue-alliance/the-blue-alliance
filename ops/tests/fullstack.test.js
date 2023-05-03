import { setDefaultOptions } from "expect-puppeteer";
import "regenerator-runtime/runtime";

jest.setTimeout(10000);
setDefaultOptions({ timeout: 10000 });

describe("Homepage", () => {
  beforeAll(async () => {
    await page.goto("http://localhost:8080");
    await page.waitForSelector(".navbar");
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

/* TODO: reenable
describe("GameDay", () => {
  beforeAll(async () => {
    await page.goto("http://localhost:8080/gameday");
    await page.waitForSelector(".gameday");
  });

  it('should be titled "GameDay - The Blue Alliance"', async () => {
    await expect(page.title()).resolves.toMatch("GameDay - The Blue Alliance");
  });

  it('should render "Select a layout"', async () => {
    await expect(page).toMatchTextContent("Select a layout");
  });
});
*/

describe("APIv3 Docs", () => {
  beforeAll(async () => {
    await page.goto("http://localhost:8080/apidocs/v3");
    await page.waitForSelector("#swagger_url");
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

/* TODO: reenable
describe("EventWizard2", () => {
  beforeAll(async () => {
    await page.goto("http://localhost:8080/eventwizard2");
    await page.waitForSelector("#eventwizard");
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
*/
