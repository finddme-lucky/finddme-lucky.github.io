// spec §8.3 — 주 1회 추첨 + 다음 날 09:00 재시도까지 여유를 둔 값.
export const STALE_DAYS = 9;

const KST_SHIFT = 9 * 3600 * 1000;
const DAY = 24 * 3600 * 1000;

const kstDay = (at) => new Date(at.getTime() + KST_SHIFT).toISOString().slice(0, 10);

export function daysSince(latestDate, now) {
  const drawn = Date.parse(`${latestDate}T00:00:00+09:00`);
  if (Number.isNaN(drawn)) throw new Error(`날짜를 읽을 수 없음: ${latestDate}`);
  const today = Date.parse(`${kstDay(now)}T00:00:00+09:00`);
  return Math.round((today - drawn) / DAY);
}

export function staleness(latestDate, now) {
  const days = daysSince(latestDate, now);
  return { days, stale: days > STALE_DAYS };
}
