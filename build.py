"""Build the public website into dist.

  python build.py                       # default URLs, no contact button
  CONTACT_EMAIL=hei@example.no python build.py

Needs Pillow (with AVIF), fontTools and brotli. Everything the page needs is
self-hosted: subset Inter fonts, AVIF/WebP images in several widths, inline
CSS and JS covered by a strict Content-Security-Policy in _headers.
"""
from __future__ import annotations

import base64
import hashlib
import html
import os
import re
import shutil
import sys
from pathlib import Path

from fontTools import subset
from PIL import Image

ROOT = Path(__file__).resolve().parent
SRC, ASSETS, DIST = ROOT / "src", ROOT / "assets", ROOT / "dist"

CONFIG = {
    "BRAND": os.environ.get("BRAND", "CoreFit"),
    "APP_URL": os.environ.get("APP_URL", "https://corefit-app.pages.dev"),
    "CONSOLE_URL": os.environ.get("CONSOLE_URL", "https://corefit-console.pages.dev"),
    "SITE_URL": os.environ.get("SITE_URL", "https://corefit-web.pages.dev").rstrip("/"),
}
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "").strip()

ARROW = ('<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M4 10h11m-4.5-5L15 10l-4.5 5" '
         'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')
# A plate-loaded bar seen end-on: the ledger's one mark.
LOGO = ('<svg viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="9" fill="#FF6B35"/>'
        '<path d="M8.5 11.5v9M12.5 8v16M19.5 8v16M23.5 11.5v9M12.5 16h7" stroke="#0A0A0C" stroke-width="2.6" '
        'stroke-linecap="round"/></svg>')

FONTS = [  # (file, family, weight, preload)
    ("InterDisplay-Black.ttf", "InterDisplay", 900, True),
    ("InterDisplay-ExtraBold.ttf", "InterDisplay", 800, False),
    ("Inter-Regular.ttf", "Inter", 400, True),
    ("Inter-SemiBold.ttf", "Inter", 600, False),
]
UNICODES = "U+0000-00FF,U+0131,U+0152-0153,U+2013-2014,U+2018-201E,U+2022,U+2026,U+2032-2033,U+2039-203A,U+2192,U+2212"

PHOTO_WIDTHS = (640, 960, 1280, 1920, 2560)
PHONE_WIDTHS = (390, 780)
WIDE_WIDTHS = (960, 1440, 2160)


def build_fonts() -> tuple[str, list[str]]:
    out = DIST / "fonts"
    out.mkdir(parents=True)
    faces, preloads = [], []
    for file, family, weight, preload in FONTS:
        name = Path(file).stem + ".woff2"
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga", "calt", "tnum", "zero", "cv11", "case", "ss01"]
        opts.name_IDs = ["*"]
        font = subset.load_font(str(ASSETS / "fonts" / file), opts)
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=subset.parse_unicodes(UNICODES))
        sub.subset(font)
        subset.save_font(font, str(out / name), opts)
        faces.append(f'@font-face{{font-family:"{family}";src:url(fonts/{name}) format("woff2");'
                     f'font-weight:{weight};font-style:normal;font-display:swap;unicode-range:{UNICODES}}}')
        if preload:
            preloads.append(f'<link rel="preload" href="fonts/{name}" as="font" type="font/woff2" crossorigin>')
    return "\n".join(faces), preloads


def encode(im: Image.Image, stem: str, widths: tuple[int, ...]) -> tuple[list[tuple[int, str, str]], tuple[int, int]]:
    out = DIST / "img"
    out.mkdir(exist_ok=True)
    made = []
    usable = [w for w in widths if w <= im.width] or [im.width]
    for w in usable:
        h = round(im.height * w / im.width)
        r = im.resize((w, h), Image.LANCZOS)
        avif, webp = f"{stem}-{w}.avif", f"{stem}-{w}.webp"
        if not (out / avif).exists():
            r.save(out / avif, quality=52, speed=4)
            r.save(out / webp, quality=74, method=6)
        made.append((w, avif, webp))
    return made, im.size


def picture(made, size, sizes, alt, cls, eager) -> str:
    w, h = size
    avif = ", ".join(f"img/{a} {wd}w" for wd, a, _ in made)
    webp = ", ".join(f"img/{b} {wd}w" for wd, _, b in made)
    mid = made[min(1, len(made) - 1)][2]
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<picture><source type="image/avif" srcset="{avif}" sizes="{sizes}">'
            f'<source type="image/webp" srcset="{webp}" sizes="{sizes}">'
            f'<img src="img/{mid}" width="{w}" height="{h}" alt="{html.escape(alt)}" class="{cls}" '
            f'{load} decoding="async"></picture>')


def photo(match: re.Match, preloads: list[str]) -> str:
    name, sizes, alt, cls, eager = (match.group(1).split("|") + [""] * 5)[:5]
    im = Image.open(ASSETS / "photos" / f"{name}.jpg").convert("RGB")
    made, size = encode(im, name, PHOTO_WIDTHS)
    if eager:
        avif = ", ".join(f"img/{a} {wd}w" for wd, a, _ in made)
        preloads.insert(0, f'<link rel="preload" as="image" type="image/avif" imagesrcset="{avif}" '
                           f'imagesizes="{sizes}" fetchpriority="high">')
    return picture(made, size, sizes, alt, cls, bool(eager))


MISSING: list[str] = []


def shot(match: re.Match) -> str:
    key, alt, kind = (match.group(1).split("|") + ["", ""])[:3]
    found = sorted((ASSETS / "screens").glob(f"{key}-*.png"))
    if not found:
        MISSING.append(key)
        return f'<div class="missing" role="img" aria-label="{html.escape(alt)}">skjerm {key} mangler</div>'
    im = Image.open(found[0]).convert("RGB")
    wide = kind == "wide"
    made, size = encode(im, "shot-" + found[0].stem, WIDE_WIDTHS if wide else PHONE_WIDTHS)
    sizes = "(min-width: 60rem) 80vw, 100vw" if wide else "(min-width: 60rem) 17rem, 78vw"
    return picture(made, size, sizes, alt, "", False)


def csp_hash(text: str) -> str:
    return "'sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode() + "'"


def main() -> int:
    DIST.mkdir(exist_ok=True)
    for child in DIST.iterdir():  # empty it in place: a preview server may hold the folder open
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    faces, preloads = build_fonts()
    css = (SRC / "site.css").read_text(encoding="utf-8").replace("{{FONTFACES}}", faces)
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s*\n\s*", "", css)
    js = (SRC / "site.js").read_text(encoding="utf-8").strip()
    page = (SRC / "index.html").read_text(encoding="utf-8")
    page = re.sub(r"\{\{img:([^}]*)\}\}", lambda m: photo(m, preloads), page)
    page = re.sub(r"\{\{shot:([^}]*)\}\}", shot, page)
    contact = (f'<a class="btn" href="mailto:{html.escape(CONTACT_EMAIL)}">Ta kontakt {ARROW}</a>'
               if CONTACT_EMAIL else "")
    values = {**CONFIG, "LOGO": LOGO, "ARROW": ARROW, "CONTACT_BUTTON": contact,
              "APP_BTN_MOD": " btn--ghost" if CONTACT_EMAIL else "", "PRELOADS": "\n".join(preloads)}
    for k, v in values.items():
        page = page.replace("{{" + k + "}}", v)
    page = page.replace("{{CSS}}", css).replace("{{JS}}", js)
    left = re.findall(r"\{\{[A-Za-z_:]+", page)
    if left:
        print("unfilled placeholders:", left, file=sys.stderr)
        return 1
    (DIST / "index.html").write_text(page, encoding="utf-8")
    (DIST / "favicon.svg").write_text(LOGO.replace(' aria-hidden="true"', ' xmlns="http://www.w3.org/2000/svg"'), encoding="utf-8")
    hero = Image.open(ASSETS / "photos" / "hero.jpg").convert("RGB")
    ow = round(hero.height * 1200 / 630)
    left_x = max(0, min(hero.width - ow, round(hero.width * 0.62 - ow / 2)))
    hero.crop((left_x, 0, left_x + ow, hero.height)).resize((1200, 630), Image.LANCZOS).save(DIST / "og.jpg", quality=82)
    (DIST / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    csp = ("default-src 'none'; img-src 'self'; font-src 'self'; connect-src 'self'; "
           f"style-src {csp_hash(css)}; script-src {csp_hash(js)}; "
           "base-uri 'none'; form-action 'none'; frame-ancestors 'none'; upgrade-insecure-requests")
    (DIST / "_headers").write_text(
        "/*\n"
        f"  Content-Security-Policy: {csp}\n"
        "  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()\n"
        "  Cross-Origin-Opener-Policy: same-origin\n"
        "  Strict-Transport-Security: max-age=31536000\n"
        "/img/*\n  Cache-Control: public, max-age=31536000, immutable\n"
        "/fonts/*\n  Cache-Control: public, max-age=31536000, immutable\n",
        encoding="utf-8")
    total = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
    print(f"built {DIST} ({total // 1024} KB total, index.html {len(page.encode()) // 1024} KB)")
    if MISSING:
        print("missing screens:", ", ".join(MISSING), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
