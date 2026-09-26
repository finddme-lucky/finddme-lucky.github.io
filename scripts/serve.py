"""dev 컨테이너용 정적 서버 — Pages 배포 레이아웃(web/ + data/를 한 루트에)을 재현한다.

    docker exec finddme-lucky python scripts/serve.py
    → http://localhost:8765

배포는 Actions가 web/과 data/를 합친 아티팩트를 올린다 (spec §2.3). 여기서는 요청 경로가
data/ 로 시작하면 저장소의 data/, 나머지는 web/ 에서 읽어 같은 주소 구조를 만든다.
"""

import http.server
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DATA = ROOT / "data"
PORT = 8765


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        clean = path.split("?", 1)[0].split("#", 1)[0].lstrip("/")
        base = ROOT if clean.startswith("data/") else WEB
        target = (base / clean).resolve()
        if not any(target == root or target.is_relative_to(root) for root in (WEB, DATA)):
            return str(WEB / "index.html")
        return str(target / "index.html") if target.is_dir() else str(target)

    def end_headers(self):
        # 개발 중에는 브라우저 HTTP 캐시가 끼어들지 않게 한다 (서비스워커 캐시는 별개).
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{self.address_string()} {fmt % args}\n")


class Server(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    if not (WEB / "index.html").exists():
        sys.exit("web/index.html이 없다")
    with Server(("", PORT), Handler) as httpd:
        print(f"http://localhost:{PORT} (Ctrl+C로 종료)", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
