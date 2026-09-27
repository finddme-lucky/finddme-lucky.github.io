import { el } from "./dom.mjs";

let loading;

// 208KB짜리 번들이라 통계 탭에 처음 들어올 때만 읽는다.
export function loadChart() {
  loading ??= new Promise((resolve, reject) => {
    const tag = el("script", { src: "vendor/chart.umd.js" });
    tag.addEventListener("load", () => resolve(globalThis.Chart));
    tag.addEventListener("error", () => reject(new Error("vendor/chart.umd.js 를 불러오지 못했습니다")));
    document.head.append(tag);
  });
  return loading;
}

// 색은 CSS 토큰에서 읽는다 — 라이트/다크가 한 곳에서 정의되도록.
export function palette() {
  const style = getComputedStyle(document.documentElement);
  const read = (name, fallback) => style.getPropertyValue(name).trim() || fallback;
  return {
    ink: read("--ink", "#1b2430"),
    muted: read("--muted", "#5c6672"),
    line: read("--line", "#e2e5ea"),
    accent: read("--accent", "#2f6fd0"),
    warn: read("--warn-ink", "#7a4a00"),
  };
}

// "63~64~65~66~67~68" 처럼 합쳐진 구간은 양 끝만 남긴다.
export function bucketLabel(bucket) {
  const parts = String(bucket).split("~");
  return parts.length <= 1 ? String(bucket) : `${parts[0]}~${parts.at(-1)}`;
}

const drawn = new Set();

export function destroyCharts() {
  for (const chart of drawn) chart.destroy();
  drawn.clear();
}

export async function drawChart(canvas, config) {
  const Chart = await loadChart();
  const colors = palette();
  Chart.defaults.color = colors.muted;
  Chart.defaults.borderColor = colors.line;
  Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
  const chart = new Chart(canvas, config);
  drawn.add(chart);
  return chart;
}

// 막대 하나짜리 기본 설정. 기대값이 있으면 선으로 겹쳐 그린다.
export function barConfig(labels, values, { expected = null, label = "관측", expectedLabel = "기대" } = {}) {
  const colors = palette();
  const datasets = [
    { type: "bar", label, data: values, backgroundColor: colors.accent, borderWidth: 0 },
  ];
  if (expected) {
    datasets.push({
      type: "line", label: expectedLabel, data: expected,
      borderColor: colors.warn, borderWidth: 2, pointRadius: 0, tension: 0.2,
    });
  }
  return {
    type: "bar",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { display: Boolean(expected) } },
      scales: {
        x: { grid: { display: false }, ticks: { autoSkip: true, maxRotation: 0 } },
        y: { beginAtZero: true, grid: { color: colors.line } },
      },
    },
  };
}

export function lineConfig(labels, values, { label = "값", fill = false } = {}) {
  const colors = palette();
  return {
    type: "line",
    data: {
      labels,
      datasets: [{
        label, data: values, borderColor: colors.accent, backgroundColor: colors.accent,
        borderWidth: 1.5, pointRadius: 0, fill, tension: 0.1,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { autoSkip: true, maxTicksLimit: 8, maxRotation: 0 } },
        y: { beginAtZero: true, grid: { color: colors.line } },
      },
    },
  };
}

// 제목 + 설명 + 캔버스를 담은 카드. 캔버스를 함께 돌려준다.
export function chartCard(title, note, { height = 220 } = {}) {
  const canvas = el("canvas", { height: String(height) });
  const card = el("section", { class: "card" },
    el("h3", {}, title),
    note ? el("p", { class: "sub" }, note) : null,
    el("div", { class: "chart", style: `height:${height}px` }, canvas));
  return { card, canvas };
}
