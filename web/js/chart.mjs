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
// 막대는 --mark(마킹 자국과 같은 노랑), 기대값 선·라인차트는 --ink(흰 바탕에서 노란 선은
// 대비가 모자라 --ink로 그린다), 격자는 --rule-soft, 글자는 --quiet.
export function palette() {
  const style = getComputedStyle(document.documentElement);
  const read = (name, fallback) => style.getPropertyValue(name).trim() || fallback;
  return {
    ink: read("--ink", "#000000"),
    mark: read("--mark", "#fbc400"),
    quiet: read("--quiet", "#6b6b66"),
    line: read("--rule-soft", "#d9d9d6"),
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

// 카드 안 스위처처럼 차트 하나만 버릴 때 쓴다 — drawn에서도 지워야
// destroyCharts()가 이미 죽은 차트를 다시 destroy()하지 않는다.
export function releaseChart(chart) {
  if (!chart) return;
  chart.destroy();
  drawn.delete(chart);
}

export async function drawChart(canvas, config) {
  const Chart = await loadChart();
  const colors = palette();
  Chart.defaults.color = colors.quiet;
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
    { type: "bar", label, data: values, backgroundColor: colors.mark, borderWidth: 0 },
  ];
  if (expected) {
    datasets.push({
      type: "line", label: expectedLabel, data: expected,
      borderColor: colors.ink, borderWidth: 2, pointRadius: 0, tension: 0.2,
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

export function lineConfig(labels, values, { label = "값", fill = false, tickFormat = null } = {}) {
  const colors = palette();
  return {
    type: "line",
    data: {
      labels,
      datasets: [{
        label, data: values, borderColor: colors.ink, backgroundColor: colors.ink,
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
        y: {
          beginAtZero: true,
          grid: { color: colors.line },
          ticks: tickFormat ? { callback: tickFormat } : {},
        },
      },
    },
  };
}

// 통계 JSON에 필드 하나가 없어도 블록 하나만 짧은 오류 문구로 바뀌고 나머지는 그대로 그려지게 한다.
export async function guardCard(title, build) {
  try {
    return await build();
  } catch (error) {
    return el("section", { class: "panel" },
      el("h3", {}, title),
      el("p", { class: "error" }, `이 항목을 불러오지 못했습니다 — ${error.message}. 새로고침해 보세요.`));
  }
}

// 제목 + 설명 + 캔버스를 담은 블록(카드 테두리 없음). 캔버스를 함께 돌려준다.
export function chartBlock(title, note, { height = 220 } = {}) {
  const canvas = el("canvas", { height: String(height) });
  const card = el("section", { class: "chart-block" },
    el("h3", {}, title),
    note ? el("p", { class: "quiet" }, note) : null,
    el("div", { class: "chart", style: `height:${height}px` }, canvas));
  return { card, canvas };
}
