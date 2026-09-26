// 날짜는 항상 KST(+09:00)로 읽는다. 기기 시간대에 따라 요일이 바뀌면 안 되므로
// +9시간 옮긴 뒤 getUTC* 로 꺼낸다.
const KST_SHIFT = 9 * 3600 * 1000;
const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

function kstParts(iso) {
  const ms = Date.parse(`${iso}T00:00:00+09:00`);
  if (Number.isNaN(ms)) throw new Error(`날짜를 읽을 수 없음: ${iso}`);
  return new Date(ms + KST_SHIFT);
}

export function formatDate(iso) {
  const at = kstParts(iso);
  return `${at.getUTCFullYear()}년 ${at.getUTCMonth() + 1}월 ${at.getUTCDate()}일 (${WEEKDAYS[at.getUTCDay()]})`;
}

export function formatDateTime(iso) {
  const ms = Date.parse(iso);
  if (Number.isNaN(ms)) throw new Error(`시각을 읽을 수 없음: ${iso}`);
  const at = new Date(ms + KST_SHIFT);
  const hh = String(at.getUTCHours()).padStart(2, "0");
  const mm = String(at.getUTCMinutes()).padStart(2, "0");
  return `${at.getUTCFullYear()}-${String(at.getUTCMonth() + 1).padStart(2, "0")}-${String(at.getUTCDate()).padStart(2, "0")} ${hh}:${mm} KST`;
}

const grouped = (n) => n.toLocaleString("ko-KR");

export const formatRound = (n) => `${grouped(n)}회`;
export const formatCount = (n) => `${grouped(n)}명`;
export const formatWon = (n) => `${grouped(n)}원`;

// 억·만 단위로 줄여 쓴다. 만원 미만은 버린다 (당첨금 표시용이며 정산값이 아니다).
export function formatWonShort(won) {
  const eok = Math.floor(won / 100000000);
  const man = Math.floor((won % 100000000) / 10000);
  if (eok > 0) return man > 0 ? `${eok}억 ${grouped(man)}만원` : `${eok}억원`;
  if (man > 0) return `${grouped(man)}만원`;
  return formatWon(won);
}

export const formatPercent = (x) => `${(x * 100).toFixed(2)}%`;
