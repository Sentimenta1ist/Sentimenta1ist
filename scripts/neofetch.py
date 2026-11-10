"""Render the neofetch-style hero card: ASCII portrait + system info + live GitHub stats.

Usage: python neofetch.py <assets_dir> [demo]
Reads GITHUB_TOKEN and GH_USER from env; "demo" skips the API. Stdlib only.
"""
import datetime as dt
import html
import json
import os
import sys
import time
import urllib.request

BG0, BG1, LINE = "#0d1117", "#161b22", "#30363d"
TEXT, MUTED, DIM = "#e6edf3", "#8b949e", "#3d444d"
BLUE, CYAN, GREEN, RED = "#d2a8ff", "#ffa657", "#3fb950", "#f85149"  # head violet, keys orange
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
JOINED = dt.date(2019, 3, 3)
NBSP = "\u00a0"  # img-rendered SVG collapses plain spaces
WIDTH = 58  # chars per info line

INFO = [
    ("Uptime", None),  # filled from JOINED
    ("Host", "IBM Ireland · watsonx Orchestrate"),
    ("Kernel", "Backend engineer → AI agents"),
    ("Shell", "zsh + Claude Code"),
    ("IDE", "IntelliJ IDEA, VS Code"),
    "- Skills",
    ("Languages", "Java, Python, TypeScript, SQL"),
    ("Backend", "Spring Boot, FastAPI, Kafka, PostgreSQL"),
    ("Frontend", "React, Next.js, Vue, Chrome MV3"),
    ("AI", "LLM agents, RAG, tool calling, evals"),
    ("AI.Models", "Claude, Gemini, OpenAI"),
    ("Infra", "Docker, Kubernetes, GitHub Actions"),
    ("Observability", "OpenTelemetry, distributed tracing"),
    "- About",
    ("Languages.Real", "English, Ukrainian, Russian"),
    ("Hobbies", "drawing, piano, badminton"),
    "- Contact",
    ("X", "@sentimentGod"),
    ("LinkedIn", "alexander-ivanenko"),
    ("Web", "sentimenta1ist.github.io"),
    "- GitHub Stats",
]


def api(path, token, body=None):
    url = "https://api.github.com" + path
    req = urllib.request.Request(url, json.dumps(body).encode() if body else None,
                                 {"Authorization": f"bearer {token}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as r:
        return r.status, (json.load(r) if r.status != 204 else None)


def stats(user, token):
    q = """query($u:String!){user(login:$u){followers{totalCount}
      repositories(ownerAffiliations:OWNER,isFork:false,first:100){totalCount nodes{name stargazerCount}}
      repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST]){totalCount}}}"""
    u = api("/graphql", token, {"query": q, "variables": {"u": user}})[1]["data"]["user"]
    commits = 0
    for year in range(JOINED.year, dt.date.today().year + 1):
        cq = f"""query($u:String!){{user(login:$u){{contributionsCollection(from:"{year}-01-01T00:00:00Z",to:"{year}-12-31T23:59:59Z")
          {{totalCommitContributions restrictedContributionsCount}}}}}}"""
        c = api("/graphql", token, {"query": cq, "variables": {"u": user}})[1]["data"]["user"]["contributionsCollection"]
        commits += c["totalCommitContributions"]
    add = rem = 0
    for repo in u["repositories"]["nodes"]:
        for _ in range(6):  # GitHub computes these lazily and answers 202 first
            code, data = api(f"/repos/{user}/{repo['name']}/stats/contributors", token)
            if code == 200:
                break
            time.sleep(3)
        for c in data or []:
            if c.get("author") and c["author"]["login"].lower() == user.lower():
                add += sum(w["a"] for w in c["weeks"])
                rem += sum(w["d"] for w in c["weeks"])
    return {"repos": u["repositories"]["totalCount"], "contrib": u["repositoriesContributedTo"]["totalCount"],
            "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
            "followers": u["followers"]["totalCount"], "commits": commits, "add": add, "rem": rem}


def uptime(today):
    y, m, d = today.year - JOINED.year, today.month - JOINED.month, today.day - JOINED.day
    if d < 0:
        m -= 1
        d += (today.replace(day=1) - dt.timedelta(days=1)).day
    if m < 0:
        y, m = y - 1, m + 12
    s = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    return f"{s(y, 'year')}, {s(m, 'month')}, {s(d, 'day')}"


def esc(s):
    return html.escape(s, quote=False).replace(" ", NBSP)


def kv(key, val, colors=None):
    """One dotted-leader line as tspans; colors maps value substrings to fills."""
    dots = WIDTH - len(key) - len(val) - 4
    out = [f'<tspan fill="{CYAN}">{esc(key)}</tspan><tspan fill="{DIM}">: {"." * dots} </tspan>']
    if colors:
        for part, fill in colors:
            out.append(f'<tspan fill="{fill}">{esc(part)}</tspan>')
    else:
        out.append(f'<tspan fill="{TEXT}">{esc(val)}</tspan>')
    return "".join(out)


def render(st, art):
    fs, lh, cw = 13, 18, 7.8
    ax, ay = 40, 78
    art_fs, art_lh = 8.8, 10.4
    art_w = max(len(l) for l in art) * art_fs * 0.6
    ix = ax + art_w + 40
    lines = []
    head = "alex@sentimenta1ist"
    lines.append(f'<tspan fill="{BLUE}" font-weight="700">{head}</tspan><tspan fill="{DIM}"> {"─" * (WIDTH - len(head) - 1)}</tspan>')
    for item in INFO:
        if item is None:
            lines.append("")
        elif isinstance(item, str):
            title = item[2:]
            lines.append(f'<tspan fill="{DIM}">- </tspan><tspan fill="{BLUE}" font-weight="700">{title}</tspan>'
                         f'<tspan fill="{DIM}"> {"─" * (WIDTH - len(title) - 3)}</tspan>')
        else:
            k, v = item
            lines.append(kv(k, v if v else uptime(dt.date.today())))
    repos = f"{st['repos']} (contributed: {st['contrib']})" if st["contrib"] else str(st["repos"])
    lines.append(kv("Repos", repos))
    lines.append(kv("Stars", str(st["stars"])))
    lines.append(kv("Commits", f"{st['commits']:,}"))
    lines.append(kv("Followers", str(st["followers"])))
    a, r = f"+{st['add']:,}", f"-{st['rem']:,}"
    net = f"{st['add'] - st['rem']:,}"
    loc = f"{net} ( {a}, {r} )"
    lines.append(kv("Lines of Code", loc, [(f"{net} ( ", TEXT), (a, GREEN), (", ", TEXT), (r, RED), (" )", TEXT)]))

    info_h = len(lines) * lh
    art_h = len(art) * art_lh
    H = int(max(info_h, art_h) + ay + 46)
    W = int(ix + WIDTH * cw + 40)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG0}"/></linearGradient>
<linearGradient id="art" x1="0" y1="0" x2="0.3" y2="1"><stop offset="0" stop-color="#e6edf3"/><stop offset="1" stop-color="#8b949e"/></linearGradient>
<radialGradient id="glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{BLUE}" stop-opacity="0.22"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
<pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="{LINE}" stroke-width="0.6" opacity="0.35"/></pattern>
</defs>
<style>
.r{{animation:in .5s ease-out backwards}}
@keyframes in{{from{{opacity:0}}}}
.cur{{animation:blink 1.1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
</style>''',
         f'<rect width="{W}" height="{H}" rx="16" fill="{BG0}"/>',
         f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{LINE}"/>',
         # window chrome
         f'<path d="M0.5 44V16.5a16 16 0 0 1 16-16h{W - 33}a16 16 0 0 1 16 16V44Z" fill="{BG1}"/><line x1="0" y1="44" x2="{W}" y2="44" stroke="{LINE}"/>',
         f'<circle cx="26" cy="22" r="6" fill="#ff5f57"/><circle cx="46" cy="22" r="6" fill="#febc2e"/><circle cx="66" cy="22" r="6" fill="#28c840"/>',
         f'<text x="{W / 2}" y="27" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{MUTED}">alex@sentimenta1ist: ~ — neofetch</text>']
    o.append(f'<g font-family="{MONO}" font-size="{art_fs}" fill="url(#art)">')
    for i, l in enumerate(art):
        o.append(f'<text class="r" style="animation-delay:{i * 0.03:.2f}s" x="{ax}" y="{ay + i * art_lh:.1f}">{esc(l)}</text>')
    o.append("</g>")
    o.append(f'<g font-family="{MONO}" font-size="{fs}" xml:space="preserve">')
    base = len(art) * 0.03
    for i, l in enumerate(lines):
        if not l:
            continue
        o.append(f'<text class="r" style="animation-delay:{base + i * 0.05:.2f}s" x="{ix}" y="{ay + i * lh}" '
                 f'textLength="{WIDTH * cw:.0f}" lengthAdjust="spacing">{l}</text>')
    y = ay + len(lines) * lh + 10
    for j, c in enumerate(["#f85149", "#ffa657", "#e3b341", "#3fb950", "#79c0ff", "#d2a8ff", TEXT, DIM]):
        o.append(f'<rect class="r" style="animation-delay:{base + len(lines) * 0.05:.2f}s" x="{ix + j * 26}" y="{y}" width="22" height="12" rx="3" fill="{c}"/>')
    o.append(f'<rect class="cur" x="{ix + 8 * 26 + 6}" y="{y}" width="8" height="14" fill="{TEXT}"/>')
    o.append("</g></svg>")
    return "\n".join(o)


def main(out, mode=None):
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "..", "assets", "portrait.txt")) as f:
        art = [l.rstrip("\n") for l in f]
    if mode == "demo":
        st = {"repos": 25, "contrib": 30, "stars": 8, "followers": 8, "commits": 1234, "add": 120000, "rem": 40000}
    else:
        st = stats(os.environ["GH_USER"], os.environ["GITHUB_TOKEN"])
    with open(os.path.join(out, "neofetch.svg"), "w") as f:
        f.write(render(st, art))
    print(json.dumps(st))


if __name__ == "__main__":
    main(*sys.argv[1:3])
