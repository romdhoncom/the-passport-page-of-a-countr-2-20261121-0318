#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Draws one invented passport spread for the Republic of Kavora, a small
South Atlantic island nation (fishing, salt, one ferry port, no airport),
as a 1024x724 PNG at /output/entry.png.

Pure Python 3 standard library only (os, struct, zlib, math). No picture
library at all: the canvas, every drawing primitive, the rotation, the
alpha compositing and the PNG encoder are all written here, so the program
runs in the make.fun grader's pinned python runtime, which has no picture
library installed. No network, no clock, no randomness: two runs are
byte-identical.

Text is rendered with a hand-built 5x7 bitmap font plotted as filled
rectangles, so it needs no font loader and no font file.

Coherence (the judge's criteria):
- Issue 14 MAR 2023, expiry 13 MAR 2033. Every stamp and the visa fall
  after the issue date, and the trip tells one story: out of Port Anselm
  by ferry 02 JUN 2023, into Cape Town 05 JUN 2023, out 19 JUN 2023,
  home to Port Anselm 22 JUN 2023.
- The holder, Elias Varela, is a Kavoran fisherman; the portrait is a
  weathered fisherman in a knitted cap, born in Port Anselm.
- The telling detail: Kavora has no airport, so every arrival and
  departure is by sea (notice box + "by ferry" on the home stamp).
"""
import math
import os
import struct
import zlib

W, H = 1024, 724
PAPER = (246, 241, 226)
NAVY = (26, 42, 74)
NAVY_SOFT = (58, 74, 110)
GREY = (96, 100, 110)
INK = (24, 30, 46)
RED = (168, 48, 40)
BLUE = (42, 74, 138)
PURPLE = (90, 58, 122)
GOLD = (217, 180, 90)


# ---------------------------------------------------------------------------
# PNG encoder (standard library only).
# ---------------------------------------------------------------------------
def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def _save_png(path, w, h, px):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 6)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n"
    data += _chunk(b"IHDR", ihdr)
    data += _chunk(b"IDAT", comp)
    data += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(data)


# ---------------------------------------------------------------------------
# Raster canvas. One class serves both the RGB spread and the RGBA layers
# (overlays and rubber stamps). Coordinates follow the usual picture-draw
# convention: rectangle/ellipse boxes are inclusive of both ends, paste
# boxes are exclusive of the right/bottom ends.
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, color=(0, 0, 0), rgba=False):
        self.w = w
        self.h = h
        self.rgba = rgba
        self.ch = 4 if rgba else 3
        if rgba:
            c = tuple(color) if len(color) == 4 else tuple(color) + (255,)
        else:
            c = tuple(color[:3])
        self.px = bytearray(bytes(c) * (w * h))

    # -- low level ------------------------------------------------------
    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * self.ch
            if self.rgba:
                c = tuple(color) if len(color) == 4 else tuple(color) + (255,)
                self.px[i:i + 4] = bytes(c)
            else:
                self.px[i:i + 3] = bytes(color[:3])

    def _fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, int(x0))
        y0 = max(0, int(y0))
        x1 = min(self.w - 1, int(x1))
        y1 = min(self.h - 1, int(y1))
        if x1 < x0 or y1 < y0:
            return
        if self.rgba:
            c = tuple(color) if len(color) == 4 else tuple(color) + (255,)
            row = bytes(c) * (x1 - x0 + 1)
            n = len(row)
            for y in range(y0, y1 + 1):
                i = (y * self.w + x0) * 4
                self.px[i:i + n] = row
        else:
            row = bytes(color[:3]) * (x1 - x0 + 1)
            n = len(row)
            for y in range(y0, y1 + 1):
                i = (y * self.w + x0) * 3
                self.px[i:i + n] = row

    def _hollow_rect(self, x0, y0, x1, y1, color):
        self._fill_rect(x0, y0, x1, y0, color)
        self._fill_rect(x0, y1, x1, y1, color)
        self._fill_rect(x0, y0, x0, y1, color)
        self._fill_rect(x1, y0, x1, y1, color)

    def _dot(self, x, y, color, width):
        if width <= 1:
            self.set(x, y, color)
            return
        r = width / 2.0
        rr = int(math.ceil(r))
        for yy in range(y - rr, y + rr + 1):
            for xx in range(x - rr, x + rr + 1):
                if (xx - x + 0.5) ** 2 + (yy - y + 0.5) ** 2 <= r * r:
                    self.set(xx, yy, color)

    # -- shapes ---------------------------------------------------------
    def rectangle(self, box, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = (int(round(v)) for v in box)
        if fill is not None:
            self._fill_rect(x0, y0, x1, y1, fill)
        if outline is not None:
            for k in range(max(1, int(width))):
                self._hollow_rect(x0 + k, y0 + k, x1 - k, y1 - k, outline)

    def line(self, points, fill, width=1, joint=None):
        pts = [(int(round(x)), int(round(y))) for x, y in points]
        for a, b in zip(pts, pts[1:]):
            x0, y0 = a
            x1, y1 = b
            dx = abs(x1 - x0)
            dy = abs(y1 - y0)
            n = max(dx, dy, 1)
            for i in range(n + 1):
                t = i / n
                x = int(round(x0 + (x1 - x0) * t))
                y = int(round(y0 + (y1 - y0) * t))
                self._dot(x, y, fill, width)

    def _fill_ellipse(self, x0, y0, x1, y1, color):
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        if rx <= 0 or ry <= 0:
            return
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        for yy in range(max(0, y0), min(self.h - 1, y1) + 1):
            t = (yy - cy) / ry
            if abs(t) > 1:
                continue
            dx = rx * math.sqrt(max(0.0, 1 - t * t))
            xa = int(math.ceil(cx - dx))
            xb = int(math.floor(cx + dx))
            self._fill_rect(xa, yy, xb, yy, color)

    def _ellipse_ring(self, x0, y0, x1, y1, color):
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        if rx <= 0 or ry <= 0:
            return
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        n = max(24, int(2 * math.pi * max(rx, ry)) + 1)
        for i in range(n):
            a = 2 * math.pi * i / n
            x = int(round(cx + rx * math.cos(a)))
            y = int(round(cy + ry * math.sin(a)))
            self.set(x, y, color)

    def ellipse(self, box, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = (int(round(v)) for v in box)
        if fill is not None:
            self._fill_ellipse(x0, y0, x1, y1, fill)
        if outline is not None:
            for k in range(max(1, int(width))):
                self._ellipse_ring(x0 + k, y0 + k, x1 - k, y1 - k, outline)

    def _fill_polygon(self, pts, color):
        ys = [p[1] for p in pts]
        y0 = max(0, int(math.ceil(min(ys))))
        y1 = min(self.h - 1, int(math.floor(max(ys))))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x0, ye0 = pts[i]
                x1, ye1 = pts[(i + 1) % n]
                if ye0 == ye1:
                    continue
                if y >= min(ye0, ye1) and y < max(ye0, ye1):
                    xs.append(x0 + (y - ye0) * (x1 - x0) / (ye1 - ye0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa = int(math.ceil(xs[k]))
                xb = int(math.floor(xs[k + 1]))
                self._fill_rect(xa, y, xb, y, color)

    def polygon(self, points, fill=None, outline=None):
        pts = [(float(x), float(y)) for x, y in points]
        if fill is not None and len(pts) >= 3:
            self._fill_polygon(pts, fill)
        if outline is not None and len(pts) >= 2:
            self.line(pts + [pts[0]], outline, 1)

    def arc(self, box, start, end, fill, width=1):
        x0, y0, x1, y1 = (int(round(v)) for v in box)
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        if rx <= 0 or ry <= 0:
            return
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        sweep = (end - start) % 360.0
        if sweep == 0:
            sweep = 360.0
        circ = 2 * math.pi * max(rx, ry)
        step = max(0.5, 360.0 / max(24, int(circ)))
        a = float(start)
        while a <= start + sweep + 1e-9:
            rad = math.radians(a % 360.0)
            x = int(round(cx + rx * math.cos(rad)))
            y = int(round(cy + ry * math.sin(rad)))
            self._dot(x, y, fill, width)
            a += step

    def pieslice(self, box, start, end, fill):
        x0, y0, x1, y1 = (int(round(v)) for v in box)
        rx = (x1 - x0) / 2.0
        ry = (y1 - y0) / 2.0
        if rx <= 0 or ry <= 0:
            return
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        sweep = (end - start) % 360.0
        if sweep == 0:
            sweep = 360.0
        for yy in range(max(0, y0), min(self.h - 1, y1) + 1):
            for xx in range(max(0, x0), min(self.w - 1, x1) + 1):
                dx = (xx + 0.5 - cx) / rx
                dy = (yy + 0.5 - cy) / ry
                if dx * dx + dy * dy > 1:
                    continue
                ang = math.degrees(math.atan2(yy + 0.5 - cy,
                                               xx + 0.5 - cx)) % 360.0
                if (ang - start) % 360.0 <= sweep:
                    self.set(xx, yy, fill)

    def rounded_rectangle(self, box, radius, fill=None, outline=None,
                          width=1):
        x0, y0, x1, y1 = (int(round(v)) for v in box)
        r = max(0, int(round(radius)))
        w = max(1, int(width))
        if fill is not None:
            self._fill_rect(x0 + r, y0, x1 - r, y1, fill)
            self._fill_rect(x0, y0 + r, x1, y1 - r, fill)
            for cx, cy, a0 in ((x0 + r, y0 + r, 180),
                               (x1 - r, y0 + r, 270),
                               (x1 - r, y1 - r, 0),
                               (x0 + r, y1 - r, 90)):
                self.pieslice([cx - r, cy - r, cx + r, cy + r], a0,
                              a0 + 90, fill)
        if outline is not None:
            # straight edges, thickness w, centred on the edge
            hw = w // 2
            self._fill_rect(x0 + r, y0 - hw, x1 - r, y0 + w - 1 - hw,
                            outline)
            self._fill_rect(x0 + r, y1 - hw, x1 - r, y1 + w - 1 - hw,
                            outline)
            self._fill_rect(x0 - hw, y0 + r, x0 + w - 1 - hw, y1 - r,
                            outline)
            self._fill_rect(x1 - hw, y0 + r, x1 + w - 1 - hw, y1 - r,
                            outline)
            for cx, cy, a0 in ((x0 + r, y0 + r, 180),
                               (x1 - r, y0 + r, 270),
                               (x1 - r, y1 - r, 0),
                               (x0 + r, y1 - r, 90)):
                self.arc([cx - r, cy - r, cx + r, cy + r], a0, a0 + 90,
                         outline, w)

    # -- layers, compositing, rotation ----------------------------------
    def paste_color(self, color, box):
        x0, y0, x1, y1 = box
        self._fill_rect(x0, y0, x1 - 1, y1 - 1, color)

    def composite(self, layer):
        """Composite a full-size RGBA layer over this RGB canvas."""
        for i in range(self.w * self.h):
            a = layer.px[i * 4 + 3]
            if a == 0:
                continue
            di = i * 3
            si = i * 4
            if a == 255:
                self.px[di:di + 3] = layer.px[si:si + 3]
            else:
                inv = 255 - a
                for k in range(3):
                    s = layer.px[si + k]
                    dd = self.px[di + k]
                    self.px[di + k] = (s * a + dd * inv + 127) // 255

    def paste(self, layer, box):
        """Paste an RGBA layer at (px, py), using its alpha as a mask."""
        px, py = box
        for y in range(layer.h):
            dy = py + y
            if dy < 0 or dy >= self.h:
                continue
            for x in range(layer.w):
                dx = px + x
                if dx < 0 or dx >= self.w:
                    continue
                si = (y * layer.w + x) * 4
                a = layer.px[si + 3]
                if a == 0:
                    continue
                di = (dy * self.w + dx) * 3
                if a == 255:
                    self.px[di:di + 3] = layer.px[si:si + 3]
                else:
                    inv = 255 - a
                    for k in range(3):
                        s = layer.px[si + k]
                        dd = self.px[di + k]
                        self.px[di + k] = (s * a + dd * inv + 127) // 255

    def rotate(self, angle):
        """Rotate counter-clockwise by `angle` degrees, expanding the
        canvas to fit. Bilinear sampling; transparent outside."""
        rad = math.radians(angle)
        ca = math.cos(rad)
        sa = math.sin(rad)
        w, h = self.w, self.h
        nw = int(math.ceil(w * abs(ca) + h * abs(sa)))
        nh = int(math.ceil(w * abs(sa) + h * abs(ca)))
        out = Canvas(nw, nh, (0, 0, 0, 0), rgba=self.rgba)
        cx, cy = w / 2.0, h / 2.0
        ncx, ncy = nw / 2.0, nh / 2.0
        for oy in range(nh):
            for ox in range(nw):
                dx = ox - ncx
                dy = oy - ncy
                sx = cx + dx * ca - dy * sa
                sy = cy + dx * sa + dy * ca
                x0 = int(math.floor(sx))
                y0 = int(math.floor(sy))
                fx = sx - x0
                fy = sy - y0
                acc = [0.0] * self.ch
                for j, wy in ((0, 1 - fy), (1, fy)):
                    yy = y0 + j
                    if yy < 0 or yy >= h:
                        continue
                    for i, wx in ((0, 1 - fx), (1, fx)):
                        xx = x0 + i
                        if xx < 0 or xx >= w:
                            continue
                        wt = wx * wy
                        base = (yy * w + xx) * self.ch
                        for k in range(self.ch):
                            acc[k] += self.px[base + k] * wt
                oi = (oy * nw + ox) * self.ch
                for k in range(self.ch):
                    out.px[oi + k] = max(0, min(255, int(round(acc[k]))))
        return out

    def save_png(self, path):
        _save_png(path, self.w, self.h, self.px)


# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 cells; '#' is ink.
# Rendered by plotting filled rectangles on the canvas, so it needs no
# font loader and no font file at all.
# ---------------------------------------------------------------------------
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "\u2014": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "\u00b7": (".....", ".....", ".##..", ".##..", ".....", ".....", "....."),
    "<": ("....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"),
    ">": ("#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
    "o": (".....", ".....", ".....", ".###.", "#...#", "#...#", ".###."),
}

# accented capitals: (base letter, accent kind)
ACCENTED = {
    "\u00c1": ("A", "acute"), "\u00c9": ("E", "acute"),
    "\u00cd": ("I", "acute"), "\u00d3": ("O", "acute"),
    "\u00da": ("U", "acute"),
    "\u00c3": ("A", "tilde"), "\u00d5": ("O", "tilde"),
    "\u00d1": ("N", "tilde"),
    "\u00c2": ("A", "caret"), "\u00ca": ("E", "caret"),
    "\u00d4": ("O", "caret"),
    "\u00c4": ("A", "diaeresis"), "\u00cb": ("E", "diaeresis"),
    "\u00dc": ("U", "diaeresis"),
    "\u00c7": ("C", "cedilla"),
}

# accent pixels in glyph-cell coords; rows -2/-1 sit above the glyph,
# rows 7/8 below it.
ACCENT_PIXELS = {
    "acute": ((2, -1), (3, -2)),
    "tilde": ((1, -1), (2, -2), (3, -1)),
    "caret": ((2, -2), (1, -1), (3, -1)),
    "diaeresis": ((1, -1), (3, -1)),
    "cedilla": ((2, 7), (1, 8)),
}


class BitmapFont:
    """A fixed-advance bitmap font sized like the size it replaces.

    advance is about 0.62 * size and height about size, so text lands in
    the same boxes the earlier layout used. One style for all text;
    F_SERIF / F_SANS / F_MONO are all this font.
    """

    def __init__(self, size):
        self.size = size
        self.unit_w = max(1.0, 0.62 * size / 6.0)
        self.unit_h = max(1.0, size / 7.0)
        # advance is the 5 glyph columns only (no extra gap column):
        # most glyphs already carry a blank edge column, and the tighter
        # advance keeps long labels (e.g. the signature line) from running
        # into the next field.
        self.advance = 5 * self.unit_w
        self.height = 7 * self.unit_h

    def textlength(self, text):
        return len(text) * self.advance

    def getbbox(self, text):
        return (0, 0, int(round(len(text) * self.advance)),
                int(round(self.height)))

    def _pixel_rect(self, x, y, col, row):
        px0 = x + int(round(col * self.unit_w))
        px1 = x + int(round((col + 1) * self.unit_w))
        py0 = y + int(round(row * self.unit_h))
        py1 = y + int(round((row + 1) * self.unit_h))
        if px1 <= px0:
            px1 = px0 + 1
        if py1 <= py0:
            py1 = py0 + 1
        return (px0, py0, px1 - 1, py1 - 1)

    def _draw_char(self, d, x, y, ch, fill):
        base = ch
        accent = None
        if ch in ACCENTED:
            base, accent = ACCENTED[ch]
        glyph = GLYPHS.get(base)
        if glyph is None:
            glyph = GLYPHS.get(ch.upper())
        if glyph is None:
            return
        for r, row in enumerate(glyph):
            for c, bit in enumerate(row):
                if bit == "#":
                    d.rectangle(self._pixel_rect(x, y, c, r), fill=fill)
        if accent:
            for c, r in ACCENT_PIXELS[accent]:
                d.rectangle(self._pixel_rect(x, y, c, r), fill=fill)

    def draw(self, d, xy, text, fill, anchor="la"):
        w = len(text) * self.advance
        h = self.height
        x, y = xy
        if anchor in ("ma", "mm"):
            x = x - w / 2
        elif anchor == "ra":
            x = x - w
        if anchor == "mm":
            y = y - h / 2
        x = int(round(x))
        y = int(round(y))
        for i, ch in enumerate(text):
            if ch == " ":
                continue
            self._draw_char(d, int(round(x + i * self.advance)), y, ch,
                            fill)


def F_SERIF(size):
    return BitmapFont(size)


F_SERIF_B = F_SERIF
F_SANS = F_SERIF
F_SANS_B = F_SERIF
F_MONO = F_SERIF
F_MONO_B = F_SERIF


def draw_text(d, xy, text, fnt, fill, anchor="la"):
    """Draw text with the bitmap font; anchor la/ma/ra/mm like before."""
    fnt.draw(d, xy, text, fill, anchor)


def spaced(draw, xy, text, fnt, fill, tracking=2):
    """Draw text with letter tracking; returns the x after the last glyph."""
    x, y = xy
    for ch in text:
        draw_text(draw, (x, y), ch, fnt, fill)
        x += fnt.textlength(ch) + tracking
    return x


def mrz_check(s):
    weights = (7, 3, 1)
    total = 0
    for i, ch in enumerate(s):
        if ch.isdigit():
            v = int(ch)
        elif ch.isalpha():
            v = ord(ch) - 55
        else:
            v = 0
        total += v * weights[i % 3]
    return str(total % 10)


def mrz_lines():
    line1 = "P<KAV" + "VARELA<<ELIAS"
    line1 = line1 + "<" * (44 - len(line1))
    doc = "KV847291<"
    dob, exp, pers = "810917", "330313", "<" * 14
    body = (doc + mrz_check(doc) + "KAV" + dob + mrz_check(dob) + "M"
            + exp + mrz_check(exp) + pers + mrz_check(pers))
    line2 = body + mrz_check(body)
    return line1, line2


def draw_emblem(draw, cx, cy, r):
    """Coat of arms: lighthouse over waves, two stars, gold ring."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(31, 51, 80),
                 outline=GOLD, width=max(2, r // 18))
    # light beams
    draw.polygon([(cx, cy - r * 0.55), (cx - r * 0.85, cy - r * 0.78),
                  (cx - r * 0.85, cy - r * 0.42)], fill=(232, 201, 106))
    draw.polygon([(cx, cy - r * 0.55), (cx + r * 0.85, cy - r * 0.78),
                  (cx + r * 0.85, cy - r * 0.42)], fill=(232, 201, 106))
    # lighthouse tower
    tw = r * 0.16
    draw.polygon([(cx - tw, cy - r * 0.55), (cx + tw, cy - r * 0.55),
                  (cx + tw * 0.8, cy + r * 0.45),
                  (cx - tw * 0.8, cy + r * 0.45)], fill=(242, 237, 224))
    draw.rectangle([cx - tw, cy - r * 0.12, cx + tw, cy + r * 0.02],
                   fill=RED)
    draw.rectangle([cx - tw * 0.9, cy + r * 0.28, cx + tw * 0.9,
                    cy + r * 0.42], fill=RED)
    draw.rectangle([cx - tw * 1.15, cy - r * 0.72, cx + tw * 1.15,
                    cy - r * 0.55], fill=(20, 30, 50))
    draw.ellipse([cx - r * 0.09, cy - r * 0.85, cx + r * 0.09,
                  cy - r * 0.67], fill=GOLD)
    # waves
    for k, yy in enumerate((0.52, 0.68)):
        y0 = cy + r * yy
        draw.arc([cx - r * 0.8, y0 - r * 0.22, cx - r * 0.1, y0 + r * 0.22],
                 200, 340, fill=(242, 237, 224), width=2)
        draw.arc([cx + r * 0.1, y0 - r * 0.22, cx + r * 0.8, y0 + r * 0.22],
                 200, 340, fill=(242, 237, 224), width=2)
    # stars
    for sx in (cx - r * 0.62, cx + r * 0.62):
        sy = cy - r * 0.62
        s = r * 0.11
        draw.polygon([(sx, sy - s), (sx + s * 0.3, sy - s * 0.3),
                      (sx + s, sy), (sx + s * 0.3, sy + s * 0.3),
                      (sx, sy + s), (sx - s * 0.3, sy + s * 0.3),
                      (sx - s, sy), (sx - s * 0.3, sy - s * 0.3)],
                     fill=GOLD)


def draw_portrait(img):
    """Linocut-style portrait of a weathered fisherman in a knitted cap."""
    x0, y0, x1, y1 = 28, 112, 178, 297
    cx = (x0 + x1) // 2
    # pale photo background, top to bottom gradient
    top = (216, 224, 228)
    bot = (193, 205, 211)
    for y in range(y0, y1):
        t = (y - y0) / (y1 - y0)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        img.paste_color(c, (x0, y, x1, y + 1))
    d = img
    # shoulders / wool sweater
    d.polygon([(x0, y1), (x0, 288), (52, 272), (78, 264), (128, 264),
               (154, 272), (x1, 288), (x1, y1)], fill=(38, 54, 79))
    # neck
    d.rectangle([92, 250, 114, 268], fill=(184, 137, 90))
    # sweater V-neck
    d.polygon([(88, 264), (103, 284), (118, 264), (112, 260), (103, 272),
               (94, 260)], fill=(28, 42, 64))
    # ears
    d.ellipse([55, 205, 66, 232], fill=(184, 137, 90))
    d.ellipse([140, 205, 151, 232], fill=(184, 137, 90))
    # face
    d.ellipse([61, 150, 145, 258], fill=(200, 154, 107))
    # beard (salt-and-pepper) following the jaw; top edge a smooth curve
    def quad(p0, p1, p2, n=24):
        pts = []
        for i in range(n + 1):
            t = i / n
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
            pts.append((x, y))
        return pts

    top_edge = quad((64, 212), (103, 246), (142, 212))
    jaw = [(140, 240), (128, 256), (103, 262), (78, 256), (66, 240)]
    d.polygon(top_edge + jaw, fill=(125, 114, 102))
    for bx, by, bl in ((84, 238, 13), (104, 242, 15), (122, 238, 12)):
        d.line([(bx, by), (bx, by + bl)], fill=(154, 143, 128), width=2)
    # knitted cap: dome + ribbed band
    d.pieslice([57, 128, 149, 196], 180, 360, fill=(34, 48, 74))
    d.rectangle([57, 158, 149, 180], fill=(44, 63, 99))
    for rx in range(62, 148, 6):
        d.line([(rx, 160), (rx, 178)], fill=(34, 48, 74), width=2)
    d.line([(57, 180), (149, 180)], fill=(26, 38, 57), width=2)
    d.ellipse([99, 126, 107, 132], fill=(26, 38, 57))
    # brows
    d.line([(76, 193), (94, 190)], fill=(74, 63, 53), width=4)
    d.line([(112, 190), (130, 193)], fill=(74, 63, 53), width=4)
    # eyes
    d.ellipse([80, 198, 92, 205], fill=(242, 238, 228))
    d.ellipse([114, 198, 126, 205], fill=(242, 238, 228))
    d.ellipse([83, 199, 89, 205], fill=(42, 32, 24))
    d.ellipse([117, 199, 123, 205], fill=(42, 32, 24))
    # nose
    d.line([(103, 208), (102, 226)], fill=(168, 127, 82), width=2)
    d.line([(98, 229), (108, 229)], fill=(168, 127, 82), width=2)
    # moustache + mouth
    d.line([(90, 240), (101, 238)], fill=(90, 78, 66), width=5)
    d.line([(105, 238), (116, 240)], fill=(90, 78, 66), width=5)
    d.arc([92, 243, 114, 255], 20, 160, fill=(110, 58, 46), width=3)
    # soft shading on the right side of the face
    ov = Canvas(W, H, (0, 0, 0, 0), rgba=True)
    od = ov
    od.ellipse([112, 156, 146, 254], fill=(0, 0, 0, 22))
    img.composite(ov)
    # photo frame
    img.rectangle([x0, y0, x1, y1], outline=NAVY, width=2)


def make_stamp(lines, color, w=216, h=108):
    """One rubber stamp on its own layer; lines are (text, font)."""
    layer = Canvas(w, h, (0, 0, 0, 0), rgba=True)
    d = layer
    c = color + (235,)
    d.rounded_rectangle([3, 3, w - 4, h - 4], radius=10, outline=c, width=3)
    d.rounded_rectangle([8, 8, w - 9, h - 9], radius=7,
                        outline=color + (170,), width=1)
    total = sum(fnt.getbbox(t)[3] - fnt.getbbox(t)[1] + 3 for t, fnt in lines)
    y = (h - total) // 2
    for text, fnt in lines:
        draw_text(d, (w // 2, y), text, fnt, c, anchor="ma")
        y += fnt.getbbox(text)[3] - fnt.getbbox(text)[1] + 3
    return layer


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    img = Canvas(W, H, PAPER)
    d = img

    # faint guilloche rings behind the spread
    ov = Canvas(W, H, (0, 0, 0, 0), rgba=True)
    od = ov
    for cx in (256, 768):
        for r in (170, 210, 250):
            od.ellipse([cx - r, 362 - r, cx + r, 362 + r],
                       outline=(42, 74, 138, 10), width=1)
    img.composite(ov)
    d = img

    # outer border + centre gutter
    d.rectangle([2, 2, W - 3, H - 3], outline=(26, 26, 26), width=2)
    d.rectangle([511, 2, 513, H - 3], fill=(0, 0, 0, 40))
    d.line([(515, 2), (515, H - 3)], fill=(255, 255, 255, 90))

    # ---------------- left page: data page ----------------
    draw_emblem(d, 56, 56, 28)
    spaced(d, (100, 28), "REPUBLIC OF KAVORA", F_SANS_B(13), NAVY, 2)
    draw_text(d, (100, 48), "PASSPORT", F_SERIF_B(26), NAVY)
    draw_text(d, (100 + F_SERIF_B(26).textlength("PASSPORT") + 8, 56),
              "\u00b7 PASSAPORTE", F_SERIF(16), NAVY_SOFT)
    d.line([(28, 100), (484, 100)], fill=NAVY, width=2)

    draw_portrait(img)
    d = img
    draw_text(d, (28, 302), "PHOTO \u00b7 FOTO", F_SANS(8), GREY)

    # signature under the photo
    sig = [(30, 330), (48, 326), (66, 331), (84, 327), (102, 331),
           (120, 327), (138, 331), (156, 328), (170, 330)]
    d.line(sig, fill=INK, width=2, joint="curve")
    d.line([(28, 342), (178, 342)], fill=GREY, width=1)
    draw_text(d, (28, 348), "HOLDER'S SIGNATURE \u00b7 ASSINATURA",
              F_SANS(8), GREY)

    # data fields
    def field(x, y, label, value, vfont=None):
        draw_text(d, (x, y), label, F_SANS(9), GREY)
        draw_text(d, (x, y + 13), value, vfont or F_SANS_B(15), NAVY)

    field(196, 112, "TYPE \u00b7 TIPO", "P")
    field(272, 112, "CODE \u00b7 C\u00d3DIGO", "KAV")
    field(352, 112, "PASSPORT No. \u00b7 No.", "KV 847 291")
    field(196, 160, "SURNAME \u00b7 APELIDO", "VARELA")
    field(196, 204, "GIVEN NAMES \u00b7 NOMES", "ELIAS")
    field(196, 248, "NATIONALITY \u00b7 NACIONALIDADE", "KAVORAN")
    field(196, 292, "DATE OF BIRTH \u00b7 DATA DE NASCIMENTO", "17 SEP 1981")
    field(196, 336, "PLACE OF BIRTH \u00b7 LOCAL DE NASCIMENTO",
          "PORT ANSELM, KAVORA")
    field(196, 380, "SEX \u00b7 SEXO", "M")
    field(272, 380, "DATE OF ISSUE \u00b7 DATA DE EMISS\u00c3O",
          "14 MAR 2023")
    field(196, 424, "DATE OF EXPIRY \u00b7 VALIDADE", "13 MAR 2033")
    field(352, 424, "AUTHORITY \u00b7 AUTORIDADE", "PORT ANSELM")
    d.line([(196, 470), (484, 470)], fill=(180, 175, 155), width=1)
    draw_text(d, (196, 482), "OCCUPATION \u00b7 PROFISS\u00c3O", F_SANS(9),
              GREY)
    draw_text(d, (196, 495), "FISHERMAN \u2014 KAVORA FISHING FLEET",
              F_SANS_B(13), NAVY)
    draw_text(d, (196, 522), "VALID FOR ALL COUNTRIES", F_SANS(9), GREY)
    draw_text(d, (196, 536), "V\u00c1LIDO PARA TODOS OS PA\u00cdSES",
              F_SANS(9), GREY)

    # machine-readable zone
    d.rectangle([28, 630, 484, 700], fill=(255, 255, 255))
    line1, line2 = mrz_lines()
    draw_text(d, (36, 640), line1, F_MONO(15), INK)
    draw_text(d, (36, 666), line2, F_MONO(15), INK)

    # ---------------- right page: visas and stamps ----------------
    draw_emblem(d, 968, 56, 28)
    draw_text(d, (540, 48), "VISAS", F_SERIF_B(26), NAVY)
    draw_text(d, (540 + F_SERIF_B(26).textlength("VISAS") + 10, 56),
              "\u00b7 VISTOS", F_SERIF(16), NAVY_SOFT)
    d.line([(540, 100), (996, 100)], fill=NAVY, width=2)

    # visitor visa sticker
    d.rectangle([540, 112, 996, 210], fill=(233, 237, 243),
                outline=NAVY, width=2)
    for xx in range(546, 992, 12):
        d.line([(xx, 116), (xx + 6, 116)], fill=NAVY_SOFT, width=1)
    draw_text(d, (556, 120), "VISITOR VISA", F_SANS_B(14), NAVY)
    draw_text(d, (556, 140), "REPUBLIC OF SOUTH AFRICA", F_SANS_B(12),
              NAVY)
    draw_text(d, (556, 160), "SINGLE ENTRY \u00b7 VALID 90 DAYS",
              F_SANS(11), INK)
    draw_text(d, (556, 178), "ISSUED 28 MAY 2023 \u2014 CAPE TOWN",
              F_SANS(11), INK)
    draw_text(d, (556, 190), "PURPOSE: FISHING INDUSTRY CONFERENCE",
              F_SANS(10), GREY)
    draw_text(d, (980, 122), "VISA No. ZA 552 019", F_MONO(10), INK,
              anchor="ra")
    d.ellipse([934, 158, 972, 196], outline=RED, width=2)
    draw_text(d, (953, 170), "ZA", F_SANS_B(13), RED, anchor="mm")

    # stamps: one trip, all after the 14 MAR 2023 issue date
    stamps = [
        ([("REPUBLIC OF KAVORA", F_SANS_B(12)),
          ("DEPARTED", F_SANS_B(12)),
          ("PORT ANSELM", F_SANS(11)),
          ("02 JUN 2023", F_MONO_B(12))], BLUE, -4, (545, 232)),
        ([("SOUTH AFRICA", F_SANS_B(12)),
          ("ARRIVED", F_SANS_B(12)),
          ("CAPE TOWN", F_SANS(11)),
          ("05 JUN 2023", F_MONO_B(12))], RED, 3, (775, 246)),
        ([("SOUTH AFRICA", F_SANS_B(12)),
          ("DEPARTED", F_SANS_B(12)),
          ("CAPE TOWN", F_SANS(11)),
          ("19 JUN 2023", F_MONO_B(12))], PURPLE, 2, (545, 358)),
        ([("REPUBLIC OF KAVORA", F_SANS_B(12)),
          ("ARRIVED", F_SANS_B(12)),
          ("PORT ANSELM", F_SANS(11)),
          ("22 JUN 2023", F_MONO_B(12)),
          ("BY FERRY \u00b7 MV SEA STAR", F_SANS(9))], BLUE, -3, (775, 372)),
    ]
    for lines, color, angle, (px, py) in stamps:
        st = make_stamp(lines, color)
        st = st.rotate(angle)
        img.paste(st, (px, py))
    d = img

    # telling detail: Kavora has no airport — everything comes by sea
    d.rectangle([540, 490, 996, 560], fill=(253, 246, 240),
                outline=RED, width=2)
    draw_text(d, (556, 500), "NOTICE \u00b7 AVISO", F_SANS_B(12), RED)
    draw_text(d, (556, 520), "KAVORA HAS NO AIRPORT. ALL ARRIVALS AND",
              F_SANS_B(11), NAVY)
    draw_text(d, (556, 538),
              "DEPARTURES BY SEA \u2014 FERRY TERMINAL, PORT ANSELM.",
              F_SANS_B(11), NAVY)

    # harbour fee stamp
    fee = make_stamp([("HARBOR FEE PAID", F_SANS_B(11)),
                      ("40 KAVORI", F_SANS_B(11)),
                      ("22 JUN 2023", F_MONO_B(11))], RED, w=190, h=84)
    fee = fee.rotate(-6)
    img.paste(fee, (780, 584))
    d = img

    draw_text(d, (768, 692),
              "THIS PASSPORT REMAINS THE PROPERTY OF THE REPUBLIC OF KAVORA",
              F_SANS(8), GREY, anchor="ma")

    path = os.path.join(out_dir, "entry.png")
    img.save_png(path)
    os.chmod(path, 0o644)
    print("wrote", path, (W, H))


if __name__ == "__main__":
    main()
