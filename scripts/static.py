"""Render the static profile art: banner, project cards, stack chips, link buttons.

Usage: python static.py <assets_dir>
Output is committed; rerun only when the copy or the palette changes.
"""
import os
import sys

BG0, BG1, LINE = "#080d1a", "#0e1a35", "#1f2f55"
TEXT, MUTED, DIM = "#e8eefb", "#8fa1c4", "#5a6d94"
BLUE, CYAN = "#5b8cff", "#38bdf8"
SANS = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

DEFS = f"""<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG1}"/><stop offset="1" stop-color="{BG0}"/></linearGradient>
<linearGradient id="ac" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>
<radialGradient id="glow" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{BLUE}" stop-opacity="0.35"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
</defs>"""


def banner():
    W, H = 1200, 340
    nodes = [("trigger", 640), ("agent", 800), ("tools", 960), ("result", 1110)]
    y = 170
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', DEFS,
         f'<rect width="{W}" height="{H}" rx="16" fill="url(#bg)"/>',
         f'<pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="{LINE}" stroke-width="0.6" opacity="0.45"/></pattern>',
         f'<rect width="{W}" height="{H}" rx="16" fill="url(#grid)"/>',
         f'<circle cx="930" cy="{y}" r="260" fill="url(#glow)"/>',
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="{LINE}"/>',
         f'<text x="64" y="104" font-family="{MONO}" font-size="14" letter-spacing="3" fill="{CYAN}">SOFTWARE ENGINEER · IBM · DUBLIN</text>',
         f'<text x="62" y="176" font-family="{SANS}" font-size="62" font-weight="700" fill="{TEXT}" letter-spacing="-1.5">Alexander</text>',
         f'<text x="62" y="244" font-family="{SANS}" font-size="62" font-weight="700" fill="url(#ac)" letter-spacing="-1.5">Ivanenko</text>',
         f'<text x="64" y="288" font-family="{SANS}" font-size="19" fill="{MUTED}">Hours of manual work in, systems that run on their own out.</text>']
    # pipeline
    xs = [n[1] for n in nodes]
    o.append(f'<line x1="{xs[0]}" y1="{y}" x2="{xs[-1]}" y2="{y}" stroke="{LINE}" stroke-width="2"/>')
    o.append(f'<line x1="{xs[0]}" y1="{y}" x2="{xs[-1]}" y2="{y}" stroke="url(#ac)" stroke-width="2" stroke-dasharray="6 10">'
             f'<animate attributeName="stroke-dashoffset" from="32" to="0" dur="1.6s" repeatCount="indefinite"/></line>')
    for i, (label, x) in enumerate(nodes):
        last = i == len(nodes) - 1
        fill = "url(#ac)" if last else BG0
        o.append(f'<rect x="{x-32}" y="{y-32}" width="64" height="64" rx="16" fill="{fill}" stroke="{BLUE if not last else CYAN}" stroke-width="1.5"/>')
        o.append(f'<text x="{x}" y="{y+6}" text-anchor="middle" font-family="{MONO}" font-size="15" font-weight="700" fill="{BG0 if last else CYAN}">{i+1:02d}</text>')
        o.append(f'<text x="{x}" y="{y+64}" text-anchor="middle" font-family="{MONO}" font-size="13" letter-spacing="1" fill="{MUTED}">{label}</text>')
    o.append(f'<circle r="5" cy="{y}" fill="{TEXT}"><animate attributeName="cx" values="{xs[0]};{xs[-1]}" dur="4s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.9;1" dur="4s" repeatCount="indefinite"/></circle>')
    o.append("</svg>")
    return "\n".join(o)


PROJECTS = [
    ("crumbclear", "Chrome extension that deletes a site's cookies the moment you close its tab. Manifest V3.", "JavaScript", "#f1e05a"),
    ("vocab", "English vocabulary trainer: Gemini writes the cards, SM-2 decides when you see them again.", "Python", "#4b8bbe"),
    ("transcribator", "YouTube link in, transcript and a ready LLM prompt out. Decide in 30 seconds.", "Python", "#4b8bbe"),
    ("memoir", "Evening journal as a PWA: three short blocks a day with photos. FastAPI + React.", "TypeScript", "#3178c6"),
    ("x-viral-radar", "Scores posts in your X feed by how likely they are to take off, while you scroll.", "JavaScript", "#f1e05a"),
    ("diet-dash", "Web app for nutritionists: profiles, meal plans, 9.9k products, docx and xlsx export.", "JavaScript", "#f1e05a"),
]


def wrap(s, n):
    lines, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + [cur]


def card(name, desc, lang, color):
    W, H = 440, 132
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', DEFS,
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="url(#bg)" stroke="{LINE}"/>',
         f'<rect x="24" y="0" width="56" height="2" fill="url(#ac)"/>',
         f'<text x="24" y="38" font-family="{MONO}" font-size="17" font-weight="700" fill="{TEXT}">{name}</text>',
         f'<text x="{W-24}" y="38" text-anchor="end" font-family="{MONO}" font-size="16" fill="{BLUE}">↗</text>']
    for i, line in enumerate(wrap(desc, 52)[:3]):
        o.append(f'<text x="24" y="{62+i*19}" font-family="{SANS}" font-size="13.5" fill="{MUTED}">{line}</text>')
    o.append(f'<circle cx="29" cy="{H-22}" r="5" fill="{color}"/>')
    o.append(f'<text x="42" y="{H-17.5}" font-family="{MONO}" font-size="12" fill="{MUTED}">{lang}</text>')
    o.append("</svg>")
    return "\n".join(o)


def chips(items, limit=860):
    x, row, o = 0, 0, []
    for it in items:
        w = len(it) * 8.2 + 28
        if x + w > limit:
            x, row = 0, row + 1
        top = row * 42
        o.append(f'<rect x="{x+0.5:.0f}" y="{top+0.5}" width="{w:.0f}" height="32" rx="16" fill="{BG1}" stroke="{LINE}"/>')
        o.append(f'<text x="{x+w/2+0.5:.0f}" y="{top+21}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{TEXT}">{it}</text>')
        x += w + 10
    H = row * 42 + 34
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{limit}" height="{H}" viewBox="0 0 {limit} {H}">' + "".join(o) + "</svg>"


def button(label):
    w = len(label) * 9 + 44
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="38" viewBox="0 0 {w:.0f} 38">{DEFS}'
            f'<rect x="0.5" y="0.5" width="{w-1:.0f}" height="37" rx="10" fill="url(#bg)" stroke="{BLUE}"/>'
            f'<text x="{w/2:.0f}" y="24" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{TEXT}">{label}</text></svg>')


def main(out):
    os.makedirs(out, exist_ok=True)
    files = {"banner.svg": banner(), "stack.svg": chips(
        ["Java", "Spring Boot", "Kafka", "Python", "FastAPI", "TypeScript", "React", "PostgreSQL", "Docker", "LLM agents", "RAG", "OpenTelemetry"]),
        "btn-linkedin.svg": button("LinkedIn ↗"), "btn-x.svg": button("X @sentimentGod ↗")}
    for n, d, l, c in PROJECTS:
        files[f"card-{n}.svg"] = card(n, d, l, c)
    for name, svg in files.items():
        with open(os.path.join(out, name), "w") as f:
            f.write(svg)


if __name__ == "__main__":
    main(sys.argv[1])
