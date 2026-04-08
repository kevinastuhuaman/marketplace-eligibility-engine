import { expect, test, type Page, type Response } from "@playwright/test";

async function openHome(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Shop All Products" })).toBeVisible();
  await expect(page.getByPlaceholder("Search products...")).toBeVisible();
}

async function waitForCatalog(page: Page) {
  await expect(page.locator('a[href^="/product/"]').first()).toBeVisible();
}

async function openFirstProduct(page: Page) {
  const firstProductLink = page.locator('a[href^="/product/"]').first();

  await expect(firstProductLink).toBeVisible();
  await Promise.all([
    page.waitForURL(/\/product\/[^/]+$/),
    firstProductLink.click(),
  ]);
  await expect(page.getByRole("button", { name: "Check Eligibility" })).toBeVisible();
}

function isEvaluateResponse(response: Response, debug: boolean) {
  if (response.request().method() !== "POST") {
    return false;
  }

  const url = new URL(response.url());
  if (!url.pathname.endsWith("/api/v1/evaluate")) {
    return false;
  }

  return debug
    ? url.searchParams.get("debug") === "true"
    : !url.searchParams.has("debug");
}

async function runEligibilityCheck(page: Page, debug: boolean) {
  const evaluationResponse = page.waitForResponse((response) =>
    isEvaluateResponse(response, debug),
  );

  await page.getByRole("button", { name: "Check Eligibility" }).click();

  const response = await evaluationResponse;
  expect(response.ok()).toBeTruthy();
}

test.describe("Walmart frontend live smoke", () => {
  test("loads the home page", async ({ page }) => {
    await openHome(page);
    await waitForCatalog(page);
  });

  test("scenario selection navigates to a product detail page", async ({ page }) => {
    await openHome(page);

    const scenarioButton = page
      .getByRole("button")
      .filter({ hasText: /^\d+\./ })
      .first();

    await expect(scenarioButton).toBeVisible();
    await Promise.all([
      page.waitForURL(/\/product\/[^/]+$/),
      scenarioButton.click(),
    ]);

    await expect(page.getByRole("link", { name: /Back to products/i })).toBeVisible();
    await expect(page.getByRole("button", { name: "Check Eligibility" })).toBeVisible();
  });

  test("product detail runs an eligibility evaluation", async ({ page }) => {
    await openHome(page);
    await waitForCatalog(page);
    await openFirstProduct(page);
    await runEligibilityCheck(page, false);

    await expect(page.getByText(/^(Eligible|Not Eligible)$/)).toBeVisible();
    await expect(page.getByText(/\d+ rules loaded, \d+ms/)).toBeVisible();
  });

  test("tester mode sends a debug evaluation and renders the debug panel", async ({ page }) => {
    await openHome(page);

    const testerToggle = page.getByRole("switch", { name: "Toggle tester mode" });
    await testerToggle.click();
    await expect(testerToggle).toHaveAttribute("aria-checked", "true");
    await expect(page.getByText("Evaluate an item to see the rule pipeline")).toBeVisible();

    await waitForCatalog(page);
    await openFirstProduct(page);
    await runEligibilityCheck(page, true);

    await expect(page.getByRole("heading", { name: "Rule Pipeline" })).toBeVisible();
    await expect(page.getByText("Rules Loaded", { exact: true })).toBeVisible();
    await expect(page.getByText("Triggered", { exact: true })).toBeVisible();
  });
});
