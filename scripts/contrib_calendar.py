#!/usr/bin/env python3
"""Render GitHub's contribution calendar as a themed SVG (replaces the green one).

Usage: python scripts/contrib_calendar.py USER [--theme cosmo-blue] [--out assets/contrib-calendar.svg]
No token needed: it reads the public calendar GitHub already shows on your profile.
"""
import argparse, datetime as dt, html, re, sys, urllib.request

# theme: bg1, bg2, primary, accent, ice, muted
THEMES = {
    "cosmo-blue":    ("#020617", "#071536", "#0A84FF", "#38BDF8", "#E0F2FE", "#7DD3FC"),
    "nebula-violet": ("#07021A", "#1B0B45", "#7C5CFF", "#A78BFA", "#EDE9FE", "#C4B5FD"),
    "aurora-teal":   ("#021A1F", "#052E35", "#14B8A6", "#2DD4BF", "#CCFBF1", "#5EEAD4"),
    "solar-flare":   ("#020617", "#0A1530", "#0A84FF", "#FBBF24", "#FEF3C7", "#FCD34D"),
    "mono-steel":    ("#05070D", "#0D1320", "#64748B", "#E2E8F0", "#FFFFFF", "#94A3B8"),
    "ion-matrix":    ("#00080F", "#001B2B", "#00B7FF", "#00F0FF", "#E6FFFF", "#67E8F9"),
}
FONT = "'JetBrains Mono','Fira Code','SF Mono','Courier New',monospace"


def mix(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * t) for x, y in zip(pa, pb))


def fetch(user):
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions",
                                 headers={"User-Agent": "Mozilla/5.0 contrib-calendar"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def parse(page):
    """Parse GitHub's contribution calendar, supporting tooltip and aria-label markup."""
    tips = {m.group(1): html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))
            for m in re.finditer(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>(.*?)</tool-tip>', page, re.S | re.I)}
    days = {}
    for m in re.finditer(r"<td\b[^>]*>", page, re.I):
        tag = m.group(0)
        date_match = re.search(r'\bdata-date=["\'](\d{4}-\d{2}-\d{2})["\']', tag)
        if not date_match:
            continue
        level_match = re.search(r'\bdata-level=["\'](\d)["\']', tag)
        id_match = re.search(r'\bid=["\']([^"\']+)["\']', tag)
        aria_match = re.search(r'\baria-label=["\']([^"\']*)["\']', tag, re.I)
        label = html.unescape(aria_match.group(1)) if aria_match else ""
        if not label and id_match:
            label = tips.get(id_match.group(1), "")
        count_match = re.search(r"([\d,]+)\s+contributions?", label, re.I)
        count = int(count_match.group(1).replace(",", "")) if count_match else 0
        level = int(level_match.group(1)) if level_match else (1 if count else 0)
        days[date_match.group(1)] = (level, count)
    total_match = re.search(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", page, re.I)
    total = int(total_match.group(1).replace(",", "")) if total_match else sum(v[1] for v in days.values())
    return days, total

def render(days, total, theme="cosmo-blue", note=None):
    bg1, bg2, pri, acc, ice, mut = THEMES[theme]
    lvl = [mix(bg2, pri, .16), mix(bg2, pri, .5), pri, acc, ice]
    W, H, C, G, X0, Y0 = 1200, 262, 15, 4, 76, 82
    dates = sorted(days)
    cells, months, last = [], [], None
    if dates:
        first = dt.date.fromisoformat(dates[0])
        off = (first.weekday() + 1) % 7  # Sunday = 0
        for i, ds in enumerate(dates):
            d = dt.date.fromisoformat(ds)
            col, row = (i + off) // 7, (d.weekday() + 1) % 7
            level, n = days[ds]
            x, y = X0 + col * (C + G), Y0 + row * (C + G)
            if d.day <= 7 and row == 0 or (col == 0 and last is None):
                if d.month != last:
                    months.append((x, d.strftime("%b")))
                    last = d.month
            extra = ' class="pulse" style="animation-delay:%.1fs"' % ((i * 0.37) % 4) if level == 4 else ""
            fl = ' filter="url(#glow)"' if level >= 3 else ""
            stroke = f' stroke="{pri}" stroke-opacity=".28"' if level == 0 else ""
            cells.append(f'<rect x="{x}" y="{y}" width="{C}" height="{C}" rx="3" fill="{lvl[level]}"{stroke}{fl}{extra}>'
                         f'<title>{n} contributions on {ds}</title></rect>')
    else:
        for col in range(53):
            for row in range(7):
                cells.append(f'<rect x="{X0+col*(C+G)}" y="{Y0+row*(C+G)}" width="{C}" height="{C}" rx="3" fill="{lvl[0]}" stroke="{pri}" stroke-opacity=".28"/>')
    mlab = "".join(f'<text x="{x}" y="{Y0-12}" font-size="12" fill="{mut}">{m}</text>' for x, m in months)
    dlab = "".join(f'<text x="{X0-12}" y="{Y0+r*(C+G)+12}" text-anchor="end" font-size="12" fill="{mut}">{n}</text>'
                   for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    lx = 880
    legend = f'<text x="{lx-8}" y="{H-34}" text-anchor="end" font-size="12" fill="{mut}">Less</text>' + "".join(
        f'<rect x="{lx+i*(C+G)}" y="{H-46}" width="{C}" height="{C}" rx="3" fill="{c}"/>' for i, c in enumerate(lvl)) + \
        f'<text x="{lx+5*(C+G)+4}" y="{H-34}" font-size="12" fill="{mut}">More</text>'
    sub = html.escape(note) if note else f"{total:,} contributions in the last year"
    br = (f'<g stroke="{acc}" stroke-width="2" fill="none" opacity=".9"><path d="M6 24V6H24"/><path d="M{W-24} 6H{W-6}V24"/>'
          f'<path d="M6 {H-24}V{H-6}H24"/><path d="M{W-24} {H-6}H{W-6}V{H-24}"/></g>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{bg1}"/><stop offset="1" stop-color="{bg2}"/></linearGradient>
<pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="{pri}" stroke-opacity=".10"/></pattern>
<filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<style>.pulse{{animation:p 3s ease-in-out infinite}}@keyframes p{{50%{{opacity:.55}}}}</style>
<rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#grid)"/>
<text x="40" y="38" font-size="13" letter-spacing="4" fill="{mut}">/// CONTRIBUTION MATRIX · {sub.upper()}</text>
{mlab}{dlab}{"".join(cells)}{legend}{br}
</svg>'''


def streaks(days):
    """Return (total, cur_len, cur_range, best_len, best_range) from {date: (level, count)}."""
    ds = sorted(days)
    act = [d for d in ds if days[d][0] > 0 or days[d][1] > 0]
    total = sum(days[d][1] for d in ds) or len(act)
    def rng(a, b):
        fa, fb = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
        f = lambda d: d.strftime("%b %-d")
        return f(fa) if a == b else f"{f(fa)} - {f(fb)}"
    best, best_r, run, start, prev = 0, "-", 0, None, None
    for d in act:
        cur = dt.date.fromisoformat(d)
        if prev is not None and (cur - prev).days == 1:
            run += 1
        else:
            run, start = 1, d
        if run >= best:
            best, best_r = run, rng(start, d)
        prev = cur
    cur_len, cur_r = 0, "-"
    if ds:
        last = ds[-1]
        idx = len(ds) - 1
        if not (days[last][0] > 0 or days[last][1] > 0):
            idx -= 1  # today not counted yet: streak is still alive from yesterday
        end = idx
        while idx >= 0 and (days[ds[idx]][0] > 0 or days[ds[idx]][1] > 0):
            idx -= 1
        cur_len = end - idx
        if cur_len:
            cur_r = rng(ds[idx + 1], ds[end])
    return total, cur_len, cur_r, best, best_r


def render_streak(days, theme="cosmo-blue", note=None):
    bg1, bg2, pri, acc, ice, mut = THEMES[theme]
    total, cl, cr, bl, br_ = streaks(days) if days else (0, 0, "-", 0, "-")
    W, H = 1200, 210
    pend = note is not None
    def panel(x, title, big, sub, col, ring=None):
        g = f'<rect x="{x}" y="46" width="360" height="132" rx="14" fill="{pri}" fill-opacity=".06" stroke="{col}" stroke-opacity=".55"/>'
        g += f'<text x="{x+24}" y="76" font-size="13" letter-spacing="4" fill="{mut}">{title}</text>'
        g += f'<text x="{x+24}" y="136" font-size="52" font-weight="800" fill="{ice}" filter="url(#glow)">{big}</text>'
        g += f'<text x="{x+24}" y="162" font-size="14" fill="{col}">{html.escape(sub)}</text>'
        if ring is not None:
            cx, cy, r = x + 296, 112, 36
            circ = 2 * 3.14159 * r
            g += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{pri}" stroke-opacity=".25" stroke-width="6"/>'
            g += (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="6" stroke-linecap="round" '
                  f'stroke-dasharray="{circ*ring:.1f} {circ:.1f}" transform="rotate(-90 {cx} {cy})" filter="url(#glow)"/>')
            g += f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="16" fill="{ice}">&#9650;</text>'
        return g
    ratio = min(1, cl / bl) if bl else 0
    tdesc = "last 12 months" if not pend else "pending first run"
    body = (panel(40, "TOTAL CONTRIBUTIONS", f"{total:,}", tdesc, acc) +
            panel(420, "CURRENT STREAK", f"{cl}", (cr if not pend else "pending first run") + (" days" if False else ""), acc, ratio) +
            panel(800, "LONGEST STREAK", f"{bl}", (br_ if not pend else "pending first run"), pri))
    brk = (f'<g stroke="{acc}" stroke-width="2" fill="none" opacity=".9"><path d="M6 24V6H24"/><path d="M{W-24} 6H{W-6}V24"/>'
           f'<path d="M6 {H-24}V{H-6}H24"/><path d="M{W-24} {H-6}H{W-6}V{H-24}"/></g>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{bg1}"/><stop offset="1" stop-color="{bg2}"/></linearGradient>
<pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="{pri}" stroke-opacity=".10"/></pattern>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#grid)"/>
<text x="40" y="30" font-size="13" letter-spacing="4" fill="{mut}">/// STREAK TRACKER · LIVE</text>
{body}{brk}
</svg>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("user")
    ap.add_argument("--theme", default="cosmo-blue", choices=THEMES)
    ap.add_argument("--out", default="assets/contrib-calendar.svg")
    ap.add_argument("--streak-out", default="assets/streak.svg")
    a = ap.parse_args()
    days, total = parse(fetch(a.user))
    if not days:
        sys.exit("No contribution days found; leaving the existing SVG untouched.")
    open(a.out, "w", encoding="utf-8").write(render(days, total, a.theme))
    open(a.streak_out, "w", encoding="utf-8").write(render_streak(days, a.theme))
    print(f"wrote {a.out}: {len(days)} days, {total} contributions")


if __name__ == "__main__":
    main()
