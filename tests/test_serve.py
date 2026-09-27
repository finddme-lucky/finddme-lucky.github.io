"""dev 정적 서버(scripts/serve.py) — 배포 레이아웃 재현과 실패 경로."""

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(scope="module")
def server():
    port = free_port()
    env = {**os.environ, "LUCKY_PORT": str(port)}
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "serve.py")],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen(f"{base}/", timeout=1).read()
                break
            except (urllib.error.URLError, ConnectionError, TimeoutError):
                time.sleep(0.05)
        else:
            raise RuntimeError("서버가 뜨지 않았다")
        yield base
    finally:
        process.terminate()
        process.wait(timeout=5)


def get(base, path, timeout=3):
    return urllib.request.urlopen(f"{base}{path}", timeout=timeout)


def test_serves_web_at_root_and_data_alongside(server):
    assert b"finddme-lucky" in get(server, "/").read()
    assert get(server, "/data/latest.json").read().startswith(b'{\n "schema"')
    assert get(server, "/js/app.mjs").headers["Content-Type"] == "text/javascript"


def test_idle_connections_do_not_block_the_server(server):
    """브라우저가 미리 열어 두는 빈 연결(preconnect)이 다른 요청을 막으면 화면이 멈춘다."""
    host = server.removeprefix("http://").split(":")
    idle = [socket.create_connection((host[0], int(host[1]))) for _ in range(6)]
    try:
        started = time.monotonic()
        assert get(server, "/data/latest.json", timeout=5).status == 200
        assert time.monotonic() - started < 2
    finally:
        for connection in idle:
            connection.close()


def raw_get(base, path):
    """urllib·curl은 ../ 를 스스로 정리해 버리므로, 가드를 시험하려면 그대로 보내야 한다."""
    host, port = base.removeprefix("http://").split(":")
    with socket.create_connection((host, int(port)), timeout=3) as connection:
        connection.sendall(
            f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode()
        )
        chunks = []
        while chunk := connection.recv(4096):
            chunks.append(chunk)
    return b"".join(chunks)


def test_paths_outside_web_and_data_are_not_served(server):
    with pytest.raises(urllib.error.HTTPError) as caught:
        get(server, "/nope.txt")
    assert caught.value.code == 404

    for path in ("/data/../lucky/store.py", "/../lucky/store.py", "/data/../../etc/passwd"):
        response = raw_get(server, path)
        assert b"404" in response.split(b"\r\n", 1)[0], path
        assert b"def save_latest" not in response and b"root:" not in response, path
