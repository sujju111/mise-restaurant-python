import { test, expect } from "@playwright/test";
test("guest request goes to staff approval; menu changes persist per owner", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Good .*chef/ }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Table 01 Available 2 seats", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Open dining session", exact: true })
    .click();
  await page.getByRole("button", { name: "Table QR", exact: true }).click();
  await page
    .getByRole("button", { name: "Open this table’s guest menu", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Add Jhol momo to order", exact: true })
    .click();
  await page.getByRole("button", { name: /View your order/ }).click();
  await page
    .getByRole("button", { name: "Send order for approval", exact: true })
    .click();
  await expect(page.getByText("Needs approval", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Close table orders", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Return to staff workspace", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Accept & send", exact: true })
    .click();
  await expect(
    page.getByText("In queue", { exact: true }).first(),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Close table visit", exact: true })
    .click();
  if (
    await page
      .getByRole("button", { name: "Open navigation", exact: true })
      .isVisible()
  )
    await page
      .getByRole("button", { name: "Open navigation", exact: true })
      .click();
  await page.getByRole("button", { name: "Menu studio", exact: true }).click();
  await page
    .getByRole("button", { name: "Edit Jhol momo", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Dish name", exact: true })
    .fill("Juniper special momo");
  await page
    .getByRole("button", { name: "Save & publish dish", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Juniper special momo", exact: true }),
  ).toBeVisible();
  await page.reload();
  await page.getByRole("button", { name: "Guest menu", exact: true }).waitFor();
  if (
    await page
      .getByRole("button", { name: "Open navigation", exact: true })
      .isVisible()
  )
    await page
      .getByRole("button", { name: "Open navigation", exact: true })
      .click();
  await page.getByRole("button", { name: "Menu studio", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Juniper special momo", exact: true }),
  ).toBeVisible();
  if (
    await page
      .getByRole("button", { name: "Open navigation", exact: true })
      .isVisible()
  )
    await page
      .getByRole("button", { name: "Open navigation", exact: true })
      .click();
  await page
    .getByRole("combobox", { name: "Restaurant workspace", exact: true })
    .press("Enter");
  await page
    .getByRole("option", { name: "Ember Kitchen", exact: true })
    .click();
  if (
    await page
      .getByRole("button", { name: "Close navigation", exact: true })
      .isVisible()
  )
    await page
      .getByRole("button", { name: "Menu studio", exact: true })
      .click();
  await expect(
    page.getByRole("heading", { name: "Jhol momo", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Juniper special momo", exact: true }),
  ).toHaveCount(0);
});
test("guest menu works without an account; no table means no ordering", async ({
  page,
}) => {
  await page.goto("/?menu=juniper-house");
  await expect(
    page.getByRole("heading", { name: "What sounds good?", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Add Jhol momo to order", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("textbox", { name: "Search guest menu", exact: true })
    .fill("chocolate");
  await expect(
    page.getByRole("heading", { name: "Chocolate fondant", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Jhol momo", exact: true }),
  ).toHaveCount(0);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});
