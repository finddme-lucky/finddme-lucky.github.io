import { balls } from "./balls.mjs";
import { el } from "./dom.mjs";
import { formatCount, formatDateTime, formatRound, formatWonShort } from "./format.mjs";
import { GAMES, gameLabel } from "./labels.mjs";
import { STALE_DAYS, staleness } from "./staleness.mjs";

const firstRank = (draw) => draw.ranks.find((rank) => rank.rank === 1);

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

// "2026년 9월 26일 토요일 추첨" — 가운뎃점으로 잇지 않는다
function drawnOn(iso) {
  const ms = Date.parse(`${iso}T00:00:00+09:00`);
  if (Number.isNaN(ms)) throw new Error(`날짜를 읽을 수 없음: ${iso}`);
  const at = new Date(ms + 9 * 3600 * 1000);
  return `${at.getUTCFullYear()}년 ${at.getUTCMonth() + 1}월 ${at.getUTCDate()}일 ${WEEKDAYS[at.getUTCDay()]}요일 추첨`;
}

function roundHeading(round) {
  return el("p", { class: "round" }, round.toLocaleString("ko-KR"), el("span", {}, "회"));
}

function staleNotice(days) {
  return el("p", { class: "notice" },
    `마지막 추첨일로부터 ${days}일이 지났는데 새 회차가 없습니다 — 데이터 갱신이 멈췄을 수 있습니다 (기준 ${STALE_DAYS}일).`);
}

function pastRounds(game, draws) {
  if (draws.length === 0) return null;
  const line = (draw) => game === "lotto645"
    ? `${formatRound(draw.round)} ${draw.numbers.join(", ")} + ${draw.bonus}`
    : `${formatRound(draw.round)} ${draw.group}조 ${draw.first}`;
  return el("details", { class: "past fine" },
    el("summary", {}, `지난 ${draws.length}회차`),
    el("ul", {}, [...draws].reverse().map((draw) => el("li", {}, line(draw)))));
}

function lottoBlock(game, section, draw, stale, days) {
  const rank = firstRank(draw);
  return el("section", { class: "block" },
    el("h2", { class: "game" }, gameLabel(game).name),
    roundHeading(section.latestRound),
    el("p", { class: "quiet" }, drawnOn(draw.date)),
    stale ? staleNotice(days) : null,
    balls(draw.numbers, draw.bonus),
    el("dl", { class: "facts" },
      el("dt", {}, "1등"), el("dd", {}, formatCount(rank.winners)),
      el("dt", {}, "1인당"), el("dd", {}, formatWonShort(rank.prize)),
      el("dt", {}, "판매액"), el("dd", {}, formatWonShort(draw.sales))),
    pastRounds(game, section.draws.slice(0, -1)));
}

function pensionBlock(game, section, draw, stale, days) {
  const rank = firstRank(draw);
  return el("section", { class: "block" },
    el("h2", { class: "game" }, gameLabel(game).name),
    roundHeading(section.latestRound),
    el("p", { class: "quiet" }, drawnOn(draw.date)),
    stale ? staleNotice(days) : null,
    el("div", { class: "digits" },
      el("em", {}, `${draw.group}조`),
      el("b", {}, [...draw.first].join(" "))),
    el("dl", { class: "facts" },
      el("dt", {}, "1등"), el("dd", {}, formatCount(rank.total)),
      el("dt", {}, "총액"), el("dd", {}, formatWonShort(rank.prize)),
      el("dt", {}, "보너스"), el("dd", {}, [...draw.bonus].join(" "))),
    pastRounds(game, section.draws.slice(0, -1)));
}

export function renderHome(target, latest, now = new Date()) {
  // 캐시에서 나온 데이터인지가 가장 확실한 신호다. navigator.onLine은 DevTools 오프라인이나
  // 서버만 죽은 경우 true로 남으므로 보조로만 쓴다.
  const servedFromCache = latest?.fromCache === true;
  const offlineBanner = el("p", { class: "notice" },
    "네트워크에 연결되지 않아 마지막으로 받은 데이터를 보여줍니다.");
  offlineBanner.hidden = !servedFromCache && navigator.onLine !== false;
  addEventListener("online", () => { offlineBanner.hidden = !servedFromCache; });
  addEventListener("offline", () => { offlineBanner.hidden = false; });
  target.append(offlineBanner);

  for (const game of Object.keys(GAMES)) {
    const section = latest.games[game];
    if (!section) continue;
    const { days, stale } = staleness(section.latestDate, now);
    const draw = section.draws.at(-1);
    target.append(game === "lotto645"
      ? lottoBlock(game, section, draw, stale, days)
      : pensionBlock(game, section, draw, stale, days));
  }

  target.append(el("p", { class: "fine" }, `데이터 변경 ${formatDateTime(latest.updatedAt)}`));
}
