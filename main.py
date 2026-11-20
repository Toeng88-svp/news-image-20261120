#!/usr/bin/env python3
"""Broadsheet front page summing up the world news of Friday 20 November 2026.

Pure Python standard library. Renders a deterministic 1024x1024 PNG and
writes it to /output/entry.png (falling back to ./entry.png when /output
is not available). No network, no clock, no randomness: two runs always
produce byte-identical output.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 233)
INK = (26, 24, 20)
ACCENT = (154, 32, 24)
MUTED = (96, 90, 80)
RULE = (70, 65, 56)
RIVER = (74, 110, 140)
FOAM = (214, 226, 233)

BUF = bytearray(bytes(PAPER) * (W * H))


def px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        BUF[i] = color[0]
        BUF[i + 1] = color[1]
        BUF[i + 2] = color[2]


def fill_rect(x0, y0, x1, y1, color):
    for y in range(y0, y1):
        for x in range(x0, x1):
            px(x, y, color)


def hline(x0, x1, y, color, thick=1):
    for t in range(thick):
        for x in range(x0, x1):
            px(x, y + t, color)


def vline(x, y0, y1, color, thick=1):
    for t in range(thick):
        for y in range(y0, y1):
            px(x + t, y, color)


def line(x0, y0, x1, y1, color, thick=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        for t in range(thick):
            px(x, y + t, color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def filled_circle(cx, cy, r, color):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                px(cx + dx, cy + dy, color)


# ---------------------------------------------------------------- font
# Classic 5x7 bitmap glyphs, rows top to bottom, 5 bits per row.
FONT = {
    "A": (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "B": (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    "C": (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    "D": (0b11100, 0b10010, 0b10001, 0b10001, 0b10001, 0b10010, 0b11100),
    "E": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    "F": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    "G": (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    "H": (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "I": (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "J": (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    "K": (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    "L": (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    "M": (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    "N": (0b10001, 0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001),
    "O": (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "P": (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    "Q": (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    "R": (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    "S": (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    "T": (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    "U": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "V": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    "W": (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b10101, 0b01010),
    "X": (0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b01010, 0b10001),
    "Y": (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    "Z": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    "0": (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    "1": (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "2": (0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111),
    "3": (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    "4": (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    "5": (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    "6": (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    "7": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    "8": (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    "9": (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0b01100, 0b01100),
    ",": (0, 0, 0, 0, 0b01100, 0b00100, 0b01000),
    "'": (0b00100, 0b00100, 0b01000, 0, 0, 0, 0),
    ":": (0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0),
    ";": (0, 0b01100, 0b01100, 0, 0b01100, 0b00100, 0b01000),
    "-": (0, 0, 0, 0b01110, 0, 0, 0),
    "—": (0, 0, 0, 0b11111, 0, 0, 0),
    "°": (0b01100, 0b10010, 0b10010, 0b01100, 0, 0, 0),
    "$": (0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100),
    "%": (0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011),
    "/": (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    "•": (0, 0, 0b01110, 0b01110, 0b01110, 0, 0),
}


def draw_char(x, y, ch, scale, color, bold=False):
    glyph = FONT.get(ch.upper(), FONT[" "])
    off = max(1, scale // 2) if bold else 0
    for row in range(7):
        bits = glyph[row]
        for col in range(5):
            if bits & (1 << (4 - col)):
                fill_rect(x + col * scale, y + row * scale,
                          x + col * scale + scale, y + row * scale + scale,
                          color)
                if off:
                    fill_rect(x + col * scale + off, y + row * scale,
                              x + col * scale + scale + off,
                              y + row * scale + scale, color)


def text_width(text, scale, bold=False):
    if not text:
        return 0
    w = len(text) * 6 * scale - scale
    if bold:
        w += max(1, scale // 2)
    return w


def draw_text(x, y, text, scale, color, bold=False):
    cx = x
    for ch in text:
        draw_char(cx, y, ch, scale, color, bold)
        cx += 6 * scale
    return cx


def draw_text_centered(y, text, scale, color, bold=False, cx=W // 2):
    x = cx - text_width(text, scale, bold) // 2
    draw_text(x, y, text, scale, color, bold)


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    cur = ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
            continue
        if cur:
            lines.append(cur)
            cur = ""
        while text_width(word, scale) > max_width:
            cut = 1
            while cut < len(word) and \
                    text_width(word[:cut + 1], scale) <= max_width:
                cut += 1
            lines.append(word[:cut])
            word = word[cut:]
        cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(x, y, text, scale, color, max_width, line_gap, bold=False):
    lines = wrap_text(text, scale, max_width)
    lh = 7 * scale + line_gap
    for i, ln in enumerate(lines):
        draw_text(x, y + i * lh, ln, scale, color, bold)
    return len(lines) * lh - line_gap


# ---------------------------------------------------------------- motif
def draw_bridge(x0, y0, x1, y1):
    """Suspension bridge over a river, with blast marks and smoke."""
    deck_y = y0 + 150
    river_y = y0 + 196
    # river
    fill_rect(x0, river_y, x1, y1, RIVER)
    for i in range(14):
        wx = x0 + 12 + (i * 37) % (x1 - x0 - 40)
        wy = river_y + 10 + (i * 23) % (y1 - river_y - 18)
        hline(wx, wx + 18, wy, FOAM, 2)
    # towers
    tw = 9
    t1x = x0 + 66
    t2x = x1 - 66 - tw
    top_y = y0 + 42
    fill_rect(t1x, top_y, t1x + tw, river_y, INK)
    fill_rect(t2x, top_y, t2x + tw, river_y, INK)
    hline(t1x - 4, t1x + tw + 4, top_y + 26, INK, 4)
    hline(t2x - 4, t2x + tw + 4, top_y + 26, INK, 4)
    # main cable, tower top to tower top, sagging to near the deck
    cx0, cx1 = t1x + tw // 2, t2x + tw // 2
    sag = deck_y - 16
    steps = 72
    for i in range(steps + 1):
        t = i / steps
        cx = int(cx0 + (cx1 - cx0) * t)
        cy = int(top_y + (sag - top_y) * (1 - (2 * t - 1) ** 2))
        fill_rect(cx - 1, cy - 1, cx + 2, cy + 2, INK)
        if i % 6 == 0 and cy + 2 < deck_y:
            vline(cx, cy + 2, deck_y, INK, 1)
    # side cables down to the deck ends
    line(x0 + 4, deck_y, cx0, top_y, INK, 2)
    line(cx1, top_y, x1 - 4, deck_y, INK, 2)
    # deck
    hline(x0, x1, deck_y, INK, 6)
    for dx in range(x0 + 14, x1 - 20, 30):
        hline(dx, dx + 14, deck_y + 14, INK, 2)
    # blast starbursts on the deck
    for bx, by, r in ((cx0 + 96, deck_y, 17), (cx1 - 130, deck_y - 2, 12)):
        for ang in range(8):
            import math
            ex = int(bx + r * math.cos(ang * math.pi / 4))
            ey = int(by + r * math.sin(ang * math.pi / 4))
            line(bx, by, ex, ey, ACCENT, 2)
    # smoke plumes
    filled_circle(cx0 + 92, deck_y - 34, 9, MUTED)
    filled_circle(cx0 + 108, deck_y - 50, 12, MUTED)
    filled_circle(cx0 + 128, deck_y - 62, 9, MUTED)
    filled_circle(cx1 - 128, deck_y - 30, 7, MUTED)
    filled_circle(cx1 - 114, deck_y - 44, 10, MUTED)


# ---------------------------------------------------------------- layout
def draw_masthead():
    draw_text_centered(26, "EST. 2026 — ONE PAGE, ONE DAY, THE WHOLE WORLD",
                       2, MUTED)
    draw_text_centered(50, "THE WORLD IN ONE PICTURE", 6, INK, bold=True)
    draw_text_centered(102, "FRIDAY 20 NOVEMBER 2026", 3, ACCENT, bold=True)
    hline(24, 1000, 132, INK, 3)
    hline(24, 1000, 138, ACCENT, 2)


def draw_lead():
    x = 24
    y = 152
    draw_text(x, y, "UKRAINE WAR — OVERNIGHT ASSAULT", 2, ACCENT, bold=True)
    draw_text(x, y + 26, "RUSSIA SMASHES KYIV'S", 5, INK, bold=True)
    draw_text(x, y + 73, "DNIPRO BRIDGES", 5, INK, bold=True)
    summary = ("Hours after the Shenzhen peace declaration, one of the "
               "war's biggest overnight assaults — some 100 missiles and "
               "400 drones, Kyiv says — hits three river bridges, "
               "killing at least three in the capital.")
    draw_wrapped(x, y + 126, summary, 2, INK, 636, 6)
    hline(24, 672, y + 216, RULE, 2)
    draw_bridge(688, 148, 1000, 388)
    hline(24, 1000, 404, INK, 3)


def draw_panel(x, y, kicker, headline, body):
    draw_text(x + 12, y + 6, kicker, 2, ACCENT, bold=True)
    draw_wrapped(x + 12, y + 24, headline, 3, INK, 460, 7, bold=True)
    draw_wrapped(x + 12, y + 80, body, 2, MUTED, 460, 4)


def draw_panels():
    draw_text(24, 418, "AROUND THE WORLD — IN BRIEF", 2, INK, bold=True)
    hline(24, 1000, 442, RULE, 2)
    panels = [
        ("CLIMATE — ANTALYA",
         "COP31 ENDS ITS FINAL DAY WITH NO DEAL",
         "Antalya summit deadlocked as phaseout language is stripped "
         "and a 1.5°C overshoot admitted; talks spill into the weekend."),
        ("DIPLOMACY",
         "ALLIES HEDGE AFTER SHENZHEN SUMMIT",
         "Canada extends its China tariff deal to 2028; Japan voices "
         "unease; Europe offers talks with Russia on Ukraine."),
        ("EUROPE — BRUSSELS",
         "BRITAIN AND EU AGREE BREXIT RESET",
         "Brussels deal: 100,000 youth visas a year each way, most "
         "food checks ended, emissions trading linked."),
        ("MARKETS",
         "ANTHROPIC SLIDES AS AI SELLOFF DEEPENS",
         "Shares fall 6% to about $91 a day after the record debut; "
         "US futures point lower."),
        ("ENERGY — HORMUZ",
         "OIL RISES, HORMUZ SHIPPING STILL CHOKED",
         "Brent $92.22 as tanker traffic stays restricted; Iran "
         "claims two tankers hit mines — unverified."),
        ("WEATHER — INDIA",
         "CYCLONE AKVAN MAKES LANDFALL IN ODISHA",
         "Storm crosses near Gopalpur with 90 km/h gusts after "
         "372,000 people are evacuated."),
    ]
    top = 452
    row_h = 150
    col_x = (24, 512)
    for i, (kick, head, body) in enumerate(panels):
        x = col_x[i % 2]
        y = top + (i // 2) * row_h
        draw_panel(x, y, kick, head, body)
    vline(506, 452, 902, RULE, 2)
    hline(24, 1000, 602, RULE, 1)
    hline(24, 1000, 752, RULE, 1)


def draw_ticker():
    fill_rect(24, 912, 1000, 1000, INK)
    ticker = ("NIGERIA MOVES TO END JAIL FOR ATTEMPTED SUICIDE • "
              "BEPICOLOMBO ARRIVES AT MERCURY THIS WEEKEND • "
              "TRUMP POSTHUMOUSLY PARDONS PETE ROSE")
    lines = wrap_text(ticker, 2, 940)
    lh = 20
    total = len(lines) * lh - 6
    y = 912 + (88 - total) // 2
    for i, ln in enumerate(lines):
        draw_text_centered(y + i * lh, ln, 2, PAPER, cx=512)


def render():
    fill_rect(10, 10, 1014, 1014, PAPER)
    for t in range(2):
        hline(10 + t, 1014 - t, 10 + t, INK, 1)
        hline(10 + t, 1014 - t, 1013 - t, INK, 1)
        vline(10 + t, 10, 1014, INK, 1)
        vline(1013 - t, 10, 1014, INK, 1)
    draw_masthead()
    draw_lead()
    draw_panels()
    draw_ticker()


# ---------------------------------------------------------------- png out
def png_bytes():
    raw = bytearray()
    row = W * 3
    for y in range(H):
        raw.append(0)
        raw += BUF[y * row:(y + 1) * row]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    render()
    data = png_bytes()
    path = "./entry.png"
    try:
        os.makedirs("/output", exist_ok=True)
        path = "/output/entry.png"
    except OSError:
        path = "./entry.png"
    try:
        with open(path, "wb") as fh:
            fh.write(data)
    except OSError:
        path = "./entry.png"
        with open(path, "wb") as fh:
            fh.write(data)
    print("wrote", path, len(data), "bytes")


if __name__ == "__main__":
    main()
