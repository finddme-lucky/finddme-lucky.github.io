export async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path} ${response.status}`);
  const document = await response.json();
  // 서비스워커가 캐시에서 내준 값이면 표시를 남긴다 (열거되지 않으므로 JSON 비교에 끼어들지 않는다).
  if (response.headers.get("X-From-Cache") === "1" && document && typeof document === "object") {
    Object.defineProperty(document, "fromCache", { value: true });
  }
  return document;
}
