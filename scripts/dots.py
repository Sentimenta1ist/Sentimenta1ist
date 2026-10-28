"""Render the last year of contributions as a heatmap in the profile palette.

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

PALETTE = ["#111a31", "#1d3a7a", "#2f62d6", "#4f8cff", "#a5c8ff"]
BG, LINE, TEXT, MUTED = "#080d1a", "#1f2f55", "#e8eefb", "#8fa1c4"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


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


def level(n, top):
    if n == 0:
        return 0
    return min(4, 1 + int(3 * math.log1p(n) / math.log1p(top) + 0.5) - (1 if n < top / 4 else 0)) if top > 1 else 1


def render(weeks):
    days = [d for w in weeks for d in w]
    total = sum(n for _, n in days)
    top = max((n for _, n in days), default=1) or 1
    cell, gap, left, head = 13, 3, 58, 100
    step = cell + gap
    width = left + step * len(weeks) + 28
    height = head + step * 7 + 54
    mono = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="16" fill="{BG}" stroke="{LINE}"/>',
           f'<text x="28" y="38" font-family="{mono}" font-size="12" letter-spacing="2.5" fill="#38bdf8">CONTRIBUTIONS · LAST 12 MONTHS</text>',
           f'<text x="28" y="62" font-family="{mono}" font-size="17" fill="{TEXT}">{total} contributions'
           f'<tspan fill="{MUTED}" font-size="14">   longest streak {longest_streak(days)} days</tspan></text>']
    for y, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="28" y="{head + y*step + 11}" font-family="{mono}" font-size="10" fill="{MUTED}">{label}</text>')
    last_month, last_x = None, -9
    for x, week in enumerate(weeks):
        month = int(week[0][0][5:7])
        if month != last_month and x - last_x >= 3 and x < len(weeks) - 2:
            out.append(f'<text x="{left + x*step}" y="{head - 8}" font-family="{mono}" font-size="10" fill="{MUTED}">{MONTHS[month-1]}</text>')
            last_x = x
        last_month = month
        for y, (date, n) in enumerate(week):
            out.append(f'<rect x="{left + x*step}" y="{head + y*step}" width="{cell}" height="{cell}" rx="3" fill="{PALETTE[level(n, top)]}">'
                       f'<title>{date}: {n}</title></rect>')
    ly = height - 22
    out.append(f'<text x="{width-28-5*step-62}" y="{ly+10}" font-family="{mono}" font-size="10" fill="{MUTED}">Less</text>')
    for i, c in enumerate(PALETTE):
        out.append(f'<rect x="{width-28-5*step-26+i*step}" y="{ly}" width="{cell}" height="{cell}" rx="3" fill="{c}"/>')
    out.append(f'<text x="{width-28-16+2}" y="{ly+10}" font-family="{mono}" font-size="10" fill="{MUTED}">More</text>')
    out.append("</svg>")
    return "\n".join(out)


def main(out_dir, mode=""):
    weeks = demo() if mode == "demo" else fetch(os.environ["GH_USER"], os.environ["GITHUB_TOKEN"])
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "heatmap.svg"), "w") as f:
        f.write(render(weeks))


if __name__ == "__main__":
    main(*sys.argv[1:3])
