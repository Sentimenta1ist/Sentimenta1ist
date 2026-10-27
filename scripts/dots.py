"""Render the last year of contributions as a dot field in the style of the profile banner.

Usage: python dots.py <out_dir> [demo]
Reads GITHUB_TOKEN and GH_USER from env; "demo" uses synthetic data.
"""
import datetime as dt
import json
import math
import os
import random
import sys
import urllib.request

QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount}}}}}}"""

THEMES = {
    "dark": dict(bg="#0b0e14", empty="#1c2230", lo="#2c4fb0", hi="#7fa2ff", text="#8b93a7", strong="#e6e9f0"),
    "light": dict(bg="#ffffff", empty="#e6e9ef", lo="#a9bff7", hi="#2f5fe0", text="#6a7283", strong="#11151c"),
}


def fetch(user, token):
    body = json.dumps({"query": QUERY, "variables": {"login": user}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", body,
                                 {"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]


def demo():
    random.seed(7)
    start = dt.date.today() - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)
    weeks, day = [], start
    while day <= dt.date.today():
        week = []
        for _ in range(7):
            if day > dt.date.today():
                break
            age = (dt.date.today() - day).days
            p = 0.15 if age > 60 else 0.85
            week.append((day.isoformat(), random.choice([1, 2, 4, 7, 12, 20]) if random.random() < p else 0))
            day += dt.timedelta(days=1)
        weeks.append(week)
    return weeks


def longest_streak(days):
    best = cur = 0
    for _, n in days:
        cur = cur + 1 if n else 0
        best = max(best, cur)
    return best


def mix(a, b, t):
    a, b = int(a[1:], 16), int(b[1:], 16)
    ch = [round(((a >> s) & 255) * (1 - t) + ((b >> s) & 255) * t) for s in (16, 8, 0)]
    return "#%02x%02x%02x" % tuple(ch)


def render(weeks, theme):
    c = THEMES[theme]
    days = [d for w in weeks for d in w]
    total = sum(n for _, n in days)
    top = max((n for _, n in days), default=1) or 1
    step, pad_x, pad_top = 16, 32, 64
    width = pad_x * 2 + step * len(weeks)
    height = pad_top + step * 7 + 28
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           f'<rect width="100%" height="100%" rx="10" fill="{c["bg"]}"/>',
           '<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}</style>',
           f'<text x="{pad_x}" y="30" font-size="11" letter-spacing="2" fill="{c["text"]}">LAST 12 MONTHS</text>',
           f'<text x="{pad_x}" y="50" font-size="15" fill="{c["strong"]}">{total} contributions'
           f'<tspan fill="{c["text"]}">  ·  longest streak {longest_streak(days)} days</tspan></text>']
    for x, week in enumerate(weeks):
        for y, (date, n) in enumerate(week):
            cx, cy = pad_x + x * step + step / 2, pad_top + y * step + step / 2
            if n == 0:
                out.append(f'<circle cx="{cx}" cy="{cy}" r="1.6" fill="{c["empty"]}"/>')
                continue
            t = math.log1p(n) / math.log1p(top)
            out.append(f'<circle cx="{cx}" cy="{cy}" r="{2.6 + 3.6 * t:.1f}" fill="{mix(c["lo"], c["hi"], t)}">'
                       f'<title>{date}: {n}</title></circle>')
    out.append("</svg>")
    return "\n".join(out)


def main(out_dir, mode=""):
    weeks = demo() if mode == "demo" else fetch(os.environ["GH_USER"], os.environ["GITHUB_TOKEN"])
    os.makedirs(out_dir, exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(out_dir, f"dots-{theme}.svg"), "w") as f:
            f.write(render(weeks, theme))


if __name__ == "__main__":
    main(*sys.argv[1:3])
