"""news-image-20261122 entry: draws /output/entry.png, a front page summing up
the world's news of 22 November 2026, using the Python standard library only.
Self-contained in one file: the grader runs python3 -P -s, which does not add
the script's own directory to sys.path, so sibling imports must not be used.
"""
import os
import struct
import zlib

# --- PNG encoder (zlib + struct only) ---------------------------------
# Picks the PNG scanline filter (None/Sub/Up/Average/Paeth) that leaves the
# smallest residual per row, the heuristic libpng uses by default: a flat
# front page compresses noticeably tighter filtered this way than with every
# row forced to filter type 0, and a smaller file wins the rules' byte-count
# tie-break.

def _chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return out + struct.pack(">I", crc)


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _residual_score(buf):
    # treat each byte as a signed delta (0..127 small, 128..255 small-negative)
    return sum(v if v < 128 else 256 - v for v in buf)


def _filter_row(raw, prev, bpp):
    width = len(raw)
    sub = bytearray(width)
    up = bytearray(width)
    avg = bytearray(width)
    paeth = bytearray(width)
    for i in range(width):
        a = raw[i - bpp] if i >= bpp else 0
        b = prev[i] if prev is not None else 0
        c = prev[i - bpp] if (prev is not None and i >= bpp) else 0
        x = raw[i]
        sub[i] = (x - a) & 0xFF
        up[i] = (x - b) & 0xFF
        avg[i] = (x - ((a + b) >> 1)) & 0xFF
        paeth[i] = (x - _paeth(a, b, c)) & 0xFF
    candidates = [(0, raw), (1, sub), (2, up), (3, avg), (4, paeth)]
    return min(candidates, key=lambda cand: _residual_score(cand[1]))


def write_png(path, width, height, rgb_rows):
    """rgb_rows: list of bytearrays, each width*3 bytes of RGB, len == height."""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    bpp = 3
    raw = bytearray()
    prev_row = None
    for row in rgb_rows:
        filter_type, filtered = _filter_row(row, prev_row, bpp)
        raw.append(filter_type)
        raw.extend(filtered)
        prev_row = row
    idat = zlib.compress(bytes(raw), 9)
    with open(path, "wb") as f:
        f.write(sig)
        f.write(_chunk(b"IHDR", ihdr))
        f.write(_chunk(b"IDAT", idat))
        f.write(_chunk(b"IEND", b""))


# --- A 5x7 monospace dot-matrix font, authored for this entry ---------
# Uppercase, digits and the punctuation this front page needs; each glyph
# is 7 rows of 5 bits.

_GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["10010", "10010", "10010", "11111", "00010", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "00000", "01100", "00110"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "'": ["01100", "01100", "01000", "00000", "00000", "00000", "00000"],
    "/": ["00001", "00001", "00010", "00100", "01000", "10000", "10000"],
}
# & $ % ! ( ) and a double quote were in the first draft of this glyph table
# but no headline on this page's final text uses them; dropped rather than
# kept as untested dead weight (glyph_rows falls back to a blank cell for an
# unknown character, so adding one back later is safe).

GLYPH_W = 5
GLYPH_H = 7


def glyph_rows(ch):
    return _GLYPHS.get(ch.upper(), _GLYPHS[" "])


# --- front page layout --------------------------------------------------

WIDTH = 1024
HEIGHT = 1024

PAPER = (247, 244, 235)
INK = (20, 18, 16)
RULE = (60, 56, 50)
RED = (150, 24, 20)
MUTED = (96, 90, 82)
TAG_BG = (20, 18, 16)
TAG_FG = (247, 244, 235)

TAG_COLORS = {
    "AMERICAS": (26, 90, 60),
    "EUROPE": (70, 40, 110),
    "AFRICA": (150, 90, 20),
    "MIDEAST": (120, 20, 20),
    "U.S.": (20, 90, 110),
    "WORLD COURT": (90, 30, 90),
}


def new_canvas(width, height, color):
    row = bytearray(color * width)
    return [bytearray(row) for _ in range(height)]


def fill_rect(rows, x, y, w, h, color):
    width = len(rows[0]) // 3
    height = len(rows)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(width, x + w), min(height, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    seg = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        rows[yy][x0 * 3:x1 * 3] = seg


def hline(rows, x, y, w, color, thickness=1):
    fill_rect(rows, x, y, w, thickness, color)


def text_width(s, scale, spacing=1):
    return len(s) * (GLYPH_W * scale + spacing) - spacing if s else 0


def draw_text(rows, x, y, s, color, scale=2, spacing=1):
    cx = x
    for ch in s:
        for gy in range(GLYPH_H):
            bits = glyph_rows(ch)[gy]
            for gx in range(GLYPH_W):
                if bits[gx] == "1":
                    fill_rect(rows, cx + gx * scale, y + gy * scale, scale, scale, color)
        cx += GLYPH_W * scale + spacing
    return cx - spacing


def draw_text_centered(rows, cx, y, s, color, scale=2, spacing=1):
    w = text_width(s, scale, spacing)
    draw_text(rows, cx - w // 2, y, s, color, scale, spacing)
    return w


def wrap_text(s, scale, max_width, spacing=1):
    words = s.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale, spacing) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_tag(rows, x, y, label, scale=2):
    pad = 7
    bg = TAG_COLORS.get(label, TAG_BG)
    w = text_width(label, scale) + pad * 2
    h = GLYPH_H * scale + pad
    fill_rect(rows, x, y, w, h, bg)
    draw_text(rows, x + pad, y + pad // 2, label, TAG_FG, scale)
    return w, h


def flow_text(rows, x, y, text, color, scale, max_width, line_gap, spacing=1):
    """Wraps text to max_width and draws it top-down; returns the y just past the last line.

    Pulled out because the page had four copies of this wrap-then-advance loop
    (main headline, its subhead, a story's headline and detail) that only
    differed in color/scale/gap, drifting out of sync whenever one was tuned.
    """
    for line in wrap_text(text, scale, max_width, spacing):
        draw_text(rows, x, y, line, color, scale, spacing)
        y += GLYPH_H * scale + line_gap
    return y


def column_positions(margin, width, count, gap):
    """count equal-width columns spanning margin..width-margin, gap apart."""
    col_w = (width - margin * 2 - gap * (count - 1)) // count
    return col_w, [margin + i * (col_w + gap) for i in range(count)]


def story_block(rows, x, y, w, tag, headline, detail, tag_scale=2, head_scale=3, detail_scale=2,
                gap=12, headline_line_gap=8, headline_gap=6, detail_line_gap=6):
    """A tagged headline + detail, the shape shared by every story on the page
    (the lead story at a bigger scale and its own spacing, and each of the
    six grid stories at a smaller one)."""
    _, th = draw_tag(rows, x, y, tag, tag_scale)
    y += th + gap
    y = flow_text(rows, x, y, headline, INK, head_scale, w, headline_line_gap)
    y += headline_gap
    return flow_text(rows, x, y, detail, MUTED, detail_scale, w, detail_line_gap)


def build():
    rows = new_canvas(WIDTH, HEIGHT, PAPER)

    # outer border
    fill_rect(rows, 0, 0, WIDTH, 10, INK)
    fill_rect(rows, 0, HEIGHT - 10, WIDTH, 10, INK)
    fill_rect(rows, 0, 0, 10, HEIGHT, INK)
    fill_rect(rows, WIDTH - 10, 0, 10, HEIGHT, INK)

    margin = 40
    content_w = WIDTH - margin * 2

    # masthead
    draw_text_centered(rows, WIDTH // 2, 40, "WORLD DAILY", INK, scale=6, spacing=3)
    hline(rows, margin, 112, content_w, INK, 4)
    draw_text_centered(rows, WIDTH // 2, 126, "SUNDAY, NOVEMBER 22, 2026", RED, scale=4, spacing=3)
    hline(rows, margin, 184, content_w, INK, 4)

    y = 212

    # lead story, at a bigger scale than the six in the grid below
    y = story_block(
        rows, margin, y, content_w,
        "SOUTH CHINA SEA",
        "CHINESE BOMBER'S FEINT TOWARD MANILA STOKES MISSILE FEARS",
        "H-6 BOMBER CAPABLE OF CARRYING CRUISE MISSILES TURNS BACK 170KM FROM THE CAPITAL NEAR A DISPUTED SHOAL",
        tag_scale=3, head_scale=4, detail_scale=3, gap=28,
        headline_line_gap=10, headline_gap=8, detail_line_gap=8,
    )

    y += 22
    hline(rows, margin, y, content_w, RULE, 2)
    y += 32

    col_w, cols_x = column_positions(margin, WIDTH, 3, 28)

    stories = [
        ("AMERICAS", "MEXICO CAPTURES CARTEL BOSS EL CHAPO ISIDRO",
         "FBI'S MOST-WANTED FUGITIVE SEIZED IN SINALOA RAID; GUNFIGHT KILLS 7 GUNMEN, 4 SOLDIERS"),
        ("EUROPE", "NATO VOWS TO DEFEND EVERY INCH OF POLAND",
         "RUTTE VISITS WARSAW AFTER RUSSIAN MISSILE FRAGMENTS FOUND ON POLISH SOIL"),
        ("AFRICA", "NIGERIA BOAT DISASTER KILLS AT LEAST 24",
         "VESSEL CARRYING MOURNERS TO A FUNERAL CAPSIZES IN BAYELSA STATE"),
        ("MIDEAST", "IRAN BEGINS RATIONING ELECTRICITY AS WAR STRAINS GRID",
         "STRIKES ON ENERGY INFRASTRUCTURE DEEPEN FUEL SHORTAGES BEFORE WINTER"),
        ("U.S.", "TRUMP DEFENDS SUMMIT TIES WITH XI AND PUTIN",
         "RETURNS HOME FROM CHINA TO FACE BIPARTISAN CRITICISM"),
        ("WORLD COURT", "ICC MOVES TO DISMISS DUTERTE DEFENSE BID",
         "PROSECUTORS SAY REQUEST VIOLATES RULES AS TRIAL NEARS ITS NOV 30 OPENING"),
    ]

    grid_top = y
    row_bottom = grid_top
    for i, (tag, headline, detail) in enumerate(stories):
        col = i % 3
        if col == 0 and i > 0:
            grid_top = row_bottom + 30
            hline(rows, margin, grid_top - 15, content_w, RULE, 1)
        yb = story_block(rows, cols_x[col], grid_top, col_w, tag, headline, detail,
                          tag_scale=2, head_scale=2, detail_scale=2, gap=10)
        row_bottom = max(row_bottom, yb)

    y = row_bottom + 28
    hline(rows, margin, y, content_w, INK, 4)
    y += 24

    draw_tag(rows, margin, y, "ALSO TODAY", 3)
    y += 56
    ticker_lines = [
        "INDIA: TOXIC ALCOHOL KILLS AT LEAST 11 IN MANIPUR, HUNDREDS HOSPITALIZED",
        "TURKEY: COP31 CLIMATE TALKS STALL AS SAUDI ARABIA BLOCKS FOSSIL FUEL PHASE-OUT TEXT",
        "DENMARK URGES EU-WIDE TRAVEL CURBS ON RUSSIANS AFTER FOILED ASSASSINATION PLOT",
    ]
    for line in ticker_lines:
        y = flow_text(rows, margin, y, line, INK, 2, content_w, 12)

    return rows, y


def main():
    rows, _used_y = build()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    write_png(out_path, WIDTH, HEIGHT, rows)


if __name__ == "__main__":
    main()
