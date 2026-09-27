"""앱 아이콘 생성 — 외부 패키지 없이 PNG를 직접 쓴다.

    docker exec finddme-lucky python scripts/make_icons.py

maskable 아이콘은 가장자리가 잘릴 수 있으므로 배경은 전면을 채우고
모양은 가운데 60% 안에만 둔다.
"""

import struct
import zlib
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "web" / "icons"
SIZES = (192, 512)
BG = (27, 36, 48)
DOTS = ((251, 196, 0), (105, 200, 242), (255, 114, 114), (170, 170, 170), (176, 216, 64), (47, 111, 208))


def write_png(path, size, pixel):
    rows = []
    for y in range(size):
        row = bytearray(b"\x00")
        for x in range(size):
            row += bytes(pixel(x, y))
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def painter(size):
    # 가운데 60% 안에 3×2로 공 6개. maskable 안전 영역(가운데 80%)을 넘지 않는다.
    span = size * 0.60
    cell_w = span / 3
    cell_h = span / 3
    left = (size - span) / 2
    top = (size - cell_h * 2) / 2
    radius = min(cell_w, cell_h) * 0.38
    centers = [
        (left + cell_w * (col + 0.5), top + cell_h * (row + 0.5))
        for row in range(2)
        for col in range(3)
    ]

    def pixel(x, y):
        # 3×3로 나눠 세어 가장자리를 부드럽게 한다 (안티에일리어싱).
        for (cx, cy), color in zip(centers, DOTS):
            covered = sum(
                1
                for sy in (0.17, 0.5, 0.83)
                for sx in (0.17, 0.5, 0.83)
                if (x + sx - cx) ** 2 + (y + sy - cy) ** 2 <= radius * radius
            )
            if covered == 9:
                return color
            if covered:
                weight = covered / 9
                return tuple(round(color[i] * weight + BG[i] * (1 - weight)) for i in range(3))
        return BG

    return pixel


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        path = OUT / f"icon-{size}.png"
        write_png(path, size, painter(size))
        print(f"{path.relative_to(OUT.parent.parent)} {path.stat().st_size:,}B")
