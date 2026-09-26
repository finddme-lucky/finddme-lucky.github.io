import { el } from "./dom.mjs";

const TIERS = [[10, "y"], [20, "b"], [30, "r"], [40, "s"], [45, "g"]];

export const ballClass = (n) => `ball ${TIERS.find(([max]) => n <= max)[1]}`;

export function balls(numbers, bonus = null) {
  return el("div", { class: "balls" },
    numbers.map((n) => el("span", { class: ballClass(n) }, n)),
    bonus === null ? null : [
      el("span", { class: "plus" }, "+"),
      el("span", { class: ballClass(bonus) }, bonus),
    ]);
}
