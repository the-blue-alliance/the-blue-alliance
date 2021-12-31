import "regenerator-runtime/runtime";

describe("Homepage", () => {
  beforeAll(async () => {
    await page.goto("http://localhost:8080");
    await page.waitForSelector(".navbar");
  });

  it('should be titled "The Blue Alliance"', async () => {
    await expect(page.title()).resolves.toMatch("The Blue Alliance");
  });

  it("should render tagline", async () => {
    await expect(page).toMatch("The Blue Alliance is the best way to scout");
  });
});

describe("GameDay", () => {
  beforeAll(async () => {
    await page.goto("http://localhost:8080/gameday");
    await page.waitForSelector(".gameday");
  });

  it('should be titled "GameDay - The Blue Alliance"', async () => {
    await expect(page.title()).resolves.toMatch("GameDay - The Blue Alliance");
  });

  it('should render "Select a layout"', async () => {
    await expect(page).toMatch("Select a layout");
  });
});
