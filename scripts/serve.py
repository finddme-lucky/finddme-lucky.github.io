"""dev 컨테이너용 정적 서버 — Pages 배포 레이아웃(web/ + data/를 한 루트에)을 재현한다.

    docker exec finddme-lucky python scripts/serve.py
    → http://localhost:8765

배포는 Actions가 web/과 data/를 합친 아티팩트를 올린다 (spec §2.3). 여기서는 요청 경로가
data/ 로 시작하면 저장소의 data/, 나머지는 web/ 에서 읽어 같은 주소 구조를 만든다.
"""

import http.server
import os
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DATA = ROOT / "data"
PORT = int(os.environ.get("LUCKY_PORT", "8765"))  # 테스트는 빈 포트를 지정해 쓴다


class Handler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # Content-Length를 항상 보내므로 연결 재사용이 안전하다
    timeout = 10  # 요청을 보내지 않는 연결을 붙잡고 있지 않는다

    def translate_path(self, path):
        clean = path.split("?", 1)[0].split("#", 1)[0].lstrip("/")
        base = ROOT if clean.startswith("data/") else WEB
        target = (base / clean).resolve()
        if not any(target == root or target.is_relative_to(root) for root in (WEB, DATA)):
            return str(WEB / "__forbidden__")  # 존재하지 않아 404가 나게 한다 (200 + index.html로 속이지 않는다)
        return str(target / "index.html") if target.is_dir() else str(target)

    def end_headers(self):
        # 개발 중에는 브라우저 HTTP 캐시가 끼어들지 않게 한다 (서비스워커 캐시는 별개).
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{self.address_string()} {fmt % args}\n")


class Server(socketserver.ThreadingTCPServer):
    # 단일 스레드면 브라우저가 미리 열어 두는 빈 연결(preconnect) 하나가 서버 전체를 붙잡아
    # 이후 요청이 전부 멈춘다. 연결마다 스레드를 쓰고, 말이 없는 연결은 제한 시간으로 끊는다.
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    if not (WEB / "index.html").exists():
        sys.exit("web/index.html이 없다")
    with Server(("", PORT), Handler) as httpd:
        print(f"http://localhost:{PORT} (Ctrl+C로 종료)", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
