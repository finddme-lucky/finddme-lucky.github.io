import { el } from "./dom.mjs";

// rules/lotto645-unpopular.json 의 gridWidth 와 같아야 한다.
// 이 격자로 lucky/rules.py 가 용지 가로줄·세로줄·대각선 패턴을 판정한다.
export const GRID_WIDTH = 7;
export const GRID_CELLS = 49;
export const NUMBERS = 45;

// 고른 번호를 용지 위의 자국으로 그린다. 숫자는 쓰지 않는다 — 모양을 보는 그림이다.
export function slipGrid(numbers, { animate = false } = {}) {
  const picked = new Set(numbers);
  const grid = el("div", { class: "slip" });
  let order = 0;
  for (let n = 1; n <= GRID_CELLS; n += 1) {
    if (n > NUMBERS) {
      grid.append(el("i", { class: "cell blank" }));
      continue;
    }
    const cell = el("i", { class: picked.has(n) ? "cell on" : "cell" });
    if (picked.has(n) && animate) {
      cell.style.setProperty("--step", String(order));
      order += 1;
    }
    grid.append(cell);
  }
  if (animate) grid.classList.add("marking");
  return grid;
}
