"""동행복권 내부 JSON 엔드포인트용 HTTP 클라이언트."""

import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from lucky.errors import NetworkError, SourceError

BASE_URL = "https://www.dhlottery.co.kr"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126 Safari/537.36"
)
RETRYABLE = (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException)


class Client:
    def __init__(
        self,
        *,
        delay=1.0,
        attempts=6,
        backoff=2.0,
        timeout=30.0,
        opener=urllib.request.urlopen,
        sleep=time.sleep,
        clock=time.monotonic,
    ):
        self.delay = delay
        self.attempts = attempts
        self.backoff = backoff
        self.timeout = timeout
        self.opener = opener
        self.sleep = sleep
        self.clock = clock
        self._last = None

    def get(self, path, params, referer):
        url = BASE_URL + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": BASE_URL + referer,
            },
        )
        error = None
        for attempt in range(self.attempts):
            self._throttle()
            try:
                with self.opener(req, timeout=self.timeout) as resp:
                    return self._decode(url, resp)
            except urllib.error.HTTPError as e:
                if e.code < 500:
                    raise SourceError(f"HTTP {e.code}: {url}") from e
                error = e
            except RETRYABLE as e:
                error = e
            if attempt < self.attempts - 1:
                self.sleep(self.backoff * 2**attempt)
        raise NetworkError(f"{self.attempts}회 시도 실패: {url} ({error!r})") from error

    def _throttle(self):
        if self._last is not None:
            wait = self.delay - (self.clock() - self._last)
            if wait > 0:
                self.sleep(wait)
        self._last = self.clock()

    @staticmethod
    def _decode(url, resp):
        final = resp.geturl()
        if final != url:
            raise SourceError(f"리다이렉트됨: {url} -> {final}")
        ctype = resp.headers.get("Content-Type", "")
        if "application/json" not in ctype:
            raise SourceError(f"JSON이 아닌 응답({ctype}): {url}")
        try:
            return json.loads(resp.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise SourceError(f"JSON 파싱 실패: {url}") from e
