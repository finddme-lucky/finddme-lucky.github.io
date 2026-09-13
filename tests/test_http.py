import urllib.error

import pytest

from lucky.errors import NetworkError, SourceError
from lucky.http import BASE_URL, Client


class FakeResp:
    def __init__(self, body, url, ctype="application/json;charset=UTF-8"):
        self._body = body.encode("utf-8")
        self._url = url
        self.headers = {"Content-Type": ctype}

    def read(self):
        return self._body

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeOpener:
    """호출마다 queue의 다음 항목을 돌려준다. 예외 인스턴스면 raise, 문자열이면 JSON 응답."""

    def __init__(self, *items):
        self.items = list(items)
        self.requests = []

    def __call__(self, req, timeout):
        self.requests.append(req)
        item = self.items.pop(0)
        if isinstance(item, BaseException):
            raise item
        if isinstance(item, FakeResp):
            return item
        return FakeResp(item, req.full_url)


def make_client(opener, **kw):
    sleeps = []
    client = Client(opener=opener, sleep=sleeps.append, clock=lambda: 0.0, **kw)
    return client, sleeps


def test_get_builds_url_headers_and_decodes_json():
    opener = FakeOpener('{"data": {"list": []}}')
    client, sleeps = make_client(opener)

    result = client.get("/lt645/x.do", {"srchDir": "latest", "srchCursorLtEpsd": 5}, "/lt645/result")

    assert result == {"data": {"list": []}}
    req = opener.requests[0]
    assert req.full_url == f"{BASE_URL}/lt645/x.do?srchDir=latest&srchCursorLtEpsd=5"
    assert req.get_header("Referer") == f"{BASE_URL}/lt645/result"
    assert req.get_header("X-requested-with") == "XMLHttpRequest"
    assert "Mozilla" in req.get_header("User-agent")
    assert sleeps == []


def test_get_without_params_has_no_query_string():
    opener = FakeOpener("{}")
    client, _ = make_client(opener)
    client.get("/pt720/list.do", {}, "/pt720/result")
    assert opener.requests[0].full_url == f"{BASE_URL}/pt720/list.do"


def test_redirect_is_source_error():
    opener = FakeOpener(FakeResp("<html></html>", f"{BASE_URL}/", "text/html; charset=UTF-8"))
    client, _ = make_client(opener)
    with pytest.raises(SourceError, match="리다이렉트"):
        client.get("/common.do", {"method": "getLottoNumber"}, "/")
    assert len(opener.requests) == 1


def test_non_json_content_type_is_source_error():
    url = f"{BASE_URL}/x.do"
    opener = FakeOpener(FakeResp("<html></html>", url, "text/html"))
    client, _ = make_client(opener)
    with pytest.raises(SourceError, match="JSON이 아닌 응답"):
        client.get("/x.do", {}, "/")


def test_invalid_json_body_is_source_error():
    opener = FakeOpener("{not json")
    client, _ = make_client(opener)
    with pytest.raises(SourceError, match="JSON 파싱 실패"):
        client.get("/x.do", {}, "/")


def test_http_4xx_is_not_retried():
    err = urllib.error.HTTPError(f"{BASE_URL}/x.do", 404, "Not Found", {}, None)
    opener = FakeOpener(err)
    client, sleeps = make_client(opener)
    with pytest.raises(SourceError, match="HTTP 404"):
        client.get("/x.do", {}, "/")
    assert len(opener.requests) == 1
    assert sleeps == []


def test_network_error_retries_then_succeeds():
    opener = FakeOpener(urllib.error.URLError(TimeoutError("timed out")), '{"ok": 1}')
    client, sleeps = make_client(opener)

    assert client.get("/x.do", {}, "/") == {"ok": 1}
    # 실패 후 백오프 2초, 두 번째 시도 전 요청 간격 1초
    assert sleeps == [2.0, 1.0]


def test_http_5xx_is_retried():
    err = urllib.error.HTTPError(f"{BASE_URL}/x.do", 503, "Unavailable", {}, None)
    opener = FakeOpener(err, '{"ok": 1}')
    client, _ = make_client(opener)
    assert client.get("/x.do", {}, "/") == {"ok": 1}
    assert len(opener.requests) == 2


def test_gives_up_after_all_attempts():
    opener = FakeOpener(TimeoutError(), ConnectionError(), TimeoutError())
    client, sleeps = make_client(opener, attempts=3)
    with pytest.raises(NetworkError, match="3회 시도 실패"):
        client.get("/x.do", {}, "/")
    assert len(opener.requests) == 3
    assert sleeps == [2.0, 1.0, 4.0, 1.0]


def test_delay_between_consecutive_requests():
    opener = FakeOpener("{}", "{}")
    client, sleeps = make_client(opener)
    client.get("/a.do", {}, "/")
    client.get("/b.do", {}, "/")
    assert sleeps == [1.0]
