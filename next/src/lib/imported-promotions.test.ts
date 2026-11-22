import { expect, it } from "vitest";
import { importedPromotionsEnabled } from "./imported-promotions";

it("ships with imported Cloud and sponsor campaigns disabled", () => {
  expect(importedPromotionsEnabled()).toBe(false);
});
