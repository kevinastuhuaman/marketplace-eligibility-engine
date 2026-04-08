import { expect, test } from "@playwright/test";

const mockItem = {
  item_id: "test-item",
  sku: "ELEC-002",
  name: "Sony WH-1000XM5 Headphones",
  category_path: "electronics.audio",
  compliance_tags: ["hazmat"],
  display_metadata: {
    emoji: "🎧",
    price: "349.99",
    description: "Wireless noise cancelling headphones with premium sound.",
  },
};

const mockSellers = [
  { seller_id: "seller-1", name: "TechGear", trust_tier: "gold" },
  { seller_id: "seller-2", name: "NewSeller", trust_tier: "silver" },
];

test.describe("Product detail responsive layout", () => {
  test("stacks cleanly on a mobile viewport", async ({ page }) => {
    await page.route("**/api/v1/items/test-item", (route) =>
      route.fulfill({ json: mockItem }),
    );
    await page.route("**/api/v1/sellers/for-item/test-item", (route) =>
      route.fulfill({ json: mockSellers }),
    );

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/product/test-item");

    await expect(page.getByRole("heading", { name: mockItem.name })).toBeVisible();
    const checkEligibility = page.getByRole("button", { name: "Check Eligibility" });
    await expect(checkEligibility).toBeVisible();

    const layout = page.locator("div.flex.flex-col.gap-6.md\\:flex-row.md\\:gap-8");
    await expect(layout).toBeVisible();

    const metrics = await page.evaluate(() => {
      const detail = document.querySelector(
        "div.flex.flex-col.gap-6.md\\:flex-row.md\\:gap-8",
      ) as HTMLDivElement | null;
      const button = Array.from(document.querySelectorAll("button")).find((node) =>
        node.textContent?.includes("Check Eligibility"),
      );
      const title = document.querySelector("h1");

      function rect(node: Element | null) {
        if (!node) return null;
        const box = node.getBoundingClientRect();
        return {
          left: box.left,
          right: box.right,
          width: box.width,
        };
      }

      return {
        innerWidth: window.innerWidth,
        detail: rect(detail),
        title: rect(title),
        button: rect(button),
      };
    });

    expect(metrics.detail).not.toBeNull();
    expect(metrics.title).not.toBeNull();
    expect(metrics.button).not.toBeNull();
    expect(metrics.detail!.right).toBeLessThanOrEqual(metrics.innerWidth);
    expect(metrics.title!.right).toBeLessThanOrEqual(metrics.innerWidth);
    expect(metrics.button!.right).toBeLessThanOrEqual(metrics.innerWidth);
  });
});
