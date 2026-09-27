// 정직성 문구가 실제로 렌더된 결과에 남아 있는지 보려면 fairnessSection()/popularitySection()을
// 직접 호출해야 한다. 이 두 함수는 web/js/dom.mjs의 el()을 통해 document.createElement 등을 쓰므로,
// 브라우저도 jsdom(설치 불가)도 없는 이 테스트 환경에서 최소한의 가짜 DOM을 흉내낸다.
// el()이 실제로 쓰는 건 createElement/createTextNode/setAttribute/append뿐이라 이 정도면 충분하다.

class FakeNode {
  constructor(tag) {
    this.tag = tag;
    this.className = "";
    this.attrs = {};
    this.children = [];
  }

  setAttribute(name, value) {
    this.attrs[name] = value;
  }

  append(...nodes) {
    this.children.push(...nodes);
  }

  get textContent() {
    return this.children.map((child) => child.textContent ?? "").join("");
  }
}

class FakeText {
  constructor(value) {
    this.value = String(value);
  }

  get textContent() {
    return this.value;
  }
}

export function installFakeDom() {
  globalThis.Node = FakeNode;
  globalThis.document = {
    createElement: (tag) => new FakeNode(tag),
    createTextNode: (value) => new FakeText(value),
  };
}
