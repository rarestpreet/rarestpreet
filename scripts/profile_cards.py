"""Generate lifetime stats, top-language and commit-history SVG cards.

Runs in .github/workflows/profile.yml. Needs GITHUB_TOKEN (a PAT with `repo`
scope as METRICS_TOKEN also counts private repos/commits).
Usage: python scripts/profile_cards.py <user> <out_dir>
"""
import json
import os
import sys
import urllib.request
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from html import escape

THEMES = {
    "dark": dict(bg="#101010", border="#242424", title="#ece7df", text="#b9b4ac",
                 muted="#7d7d7d", accent="#e01b24", bar="#e01b24", track="#1c1c1c", rx=0, spacing=4,
                 font="'JetBrains Mono', 'Fira Code', Consolas, ui-monospace, monospace"),
    "pink": dict(bg="#fff5f8", border="#f9d9dd", title="#e75480", text="#6b4a57",
                 muted="#a07a88", accent="#e75480", bar="#efadc9", track="#fde7ee",
                 rx=6, spacing=0, font="'Cutive Mono', ui-monospace, monospace"),
}
IGNORED_LANGS = {"Batchfile", "Dockerfile", "Procfile", "Makefile"}
LANG_COLORS = ["#e01b24", "#ece7df", "#8f1117", "#9a948c", "#ff5a5f", "#5c5c5c", "#5c0a0d", "#c9c3ba"]
LANG_COLORS_PINK = ["#e75480", "#efadc9", "#b388eb", "#8ecae6", "#f4a261", "#a07a88", "#ffc8dd", "#cdb4db"]


def gql(query, **variables):
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(body["errors"])
    return body["data"]


def collect(user):
    info = gql("""query($u:String!){user(login:$u){createdAt
        contributionsCollection{contributionYears}
        pullRequests{totalCount} issues{totalCount}
        repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST]){totalCount}}}""", u=user)["user"]

    commits_by_year, months, days = OrderedDict(), OrderedDict(), {}
    for year in sorted(info["contributionsCollection"]["contributionYears"]):
        c = gql("""query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){
            contributionsCollection(from:$f,to:$t){totalCommitContributions restrictedContributionsCount
              contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}""",
                u=user, f=f"{year}-01-01T00:00:00Z", t=f"{year}-12-31T23:59:59Z")["user"]["contributionsCollection"]
        commits_by_year[year] = c["totalCommitContributions"] + c["restrictedContributionsCount"]
        for w in c["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
                key = d["date"][:7]
                if key >= info["createdAt"][:7] and d["date"] <= datetime.now(timezone.utc).date().isoformat():
                    months[key] = months.get(key, 0) + d["contributionCount"]

    langs, stars, cursor = Counter(), 0, None
    while True:
        page = gql("""query($u:String!,$c:String){user(login:$u){repositories(first:100,after:$c,ownerAffiliations:OWNER,isFork:false){
            pageInfo{hasNextPage endCursor}
            nodes{stargazerCount languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}}}""",
                   u=user, c=cursor)["user"]["repositories"]
        for repo in page["nodes"]:
            stars += repo["stargazerCount"]
            for e in repo["languages"]["edges"]:
                if e["node"]["name"] not in IGNORED_LANGS:
                    langs[e["node"]["name"]] += e["size"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    return dict(
        since=info["createdAt"][:4],
        commits=sum(commits_by_year.values()),
        commits_by_year=commits_by_year,
        months=months,
        prs=info["pullRequests"]["totalCount"],
        issues=info["issues"]["totalCount"],
        contributed=info["repositoriesContributedTo"]["totalCount"],
        stars=stars,
        langs=langs,
        **streaks(days),
    )


def streaks(days):
    today = datetime.now(timezone.utc).date().isoformat()
    dates = sorted(d for d in days if d <= today)
    longest = run = 0
    for d in dates:
        run = run + 1 if days[d] else 0
        longest = max(longest, run)
    current = 0
    for i, d in enumerate(reversed(dates)):
        if days[d]:
            current += 1
        elif i > 0:  # today without contributions yet doesn't break the streak
            break
    active = sum(1 for d in dates if days[d])
    return dict(current_streak=current, longest_streak=longest, active_days=active)


def frame(t, w, h, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<style>text{{font-family:{t['font']};}} .t{{fill:{t['title']};font-size:16px;font-weight:700}}
.l{{fill:{t['text']};font-size:13px}} .m{{fill:{t['muted']};font-size:11px}} .n{{fill:{t['accent']};font-size:13px;font-weight:700}}</style>
<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{t['rx']}" fill="{t['bg']}" stroke="{t['border']}"/>
{f'<rect width="{w}" height="3" fill="{t["accent"]}"/>' if not t['rx'] else ''}
<text x="20" y="32" class="t" letter-spacing="{t['spacing']}">{escape(title)}</text>
{body}
</svg>"""


def stats_card(d, t, title):
    rows = [("Lifetime commits", d["commits"]), ("Pull requests", d["prs"]), ("Issues", d["issues"]),
            ("Contributed to", d["contributed"]), ("Stars earned", d["stars"])]
    body = "".join(
        f'<text x="20" y="{64 + i * 24}" class="l">{label}</text>'
        f'<text x="330" y="{64 + i * 24}" class="n" text-anchor="end">{value:,}</text>'
        for i, (label, value) in enumerate(rows))
    body += f'<text x="20" y="{64 + len(rows) * 24}" class="m">since {d["since"]} · ' + \
            " · ".join(f"'{str(y)[2:]} {c:,}" for y, c in d["commits_by_year"].items() if c) + "</text>"
    return frame(t, 350, 200, title, body)


def streak_card(d, t, title):
    cols = [("CURRENT", d["current_streak"], "days"), ("LONGEST", d["longest_streak"], "days"),
            ("ACTIVE", d["active_days"], "days total")]
    body = ""
    for i, (label, value, unit) in enumerate(cols):
        x = 20 + i * 108
        if i:
            body += f'<line x1="{x - 12}" y1="60" x2="{x - 12}" y2="170" stroke="{t['border']}"/>'
        body += (f'<text x="{x}" y="72" class="m" letter-spacing="2">{label}</text>'
                 f'<text x="{x}" y="128" font-size="40" font-weight="800" fill="{t['accent'] if i == 0 else t['title']}">{value:,}</text>'
                 f'<text x="{x}" y="152" class="m">{unit}</text>')
    return frame(t, 350, 200, title, body)


def langs_card(d, t, title, colors):
    top = d["langs"].most_common(8)
    total = sum(s for _, s in top) or 1
    x, bar = 20.0, ""
    for i, (_, size) in enumerate(top):
        wpx = 310 * size / total
        bar += f'<rect x="{x:.1f}" y="50" width="{wpx:.1f}" height="8" fill="{colors[i % len(colors)]}"/>'
        x += wpx
    body = f'<clipPath id="r"><rect x="20" y="50" width="310" height="8" rx="4"/></clipPath><g clip-path="url(#r)">{bar}</g>'
    for i, (name, size) in enumerate(top):
        cx, cy = 20 + (i % 2) * 160, 82 + (i // 2) * 24
        body += (f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{colors[i % len(colors)]}"/>'
                 f'<text x="{cx + 16}" y="{cy}" class="l">{escape(name)} <tspan class="m">{100 * size / total:.1f}%</tspan></text>')
    return frame(t, 350, 200, title, body)


def history_card(d, t, title):
    months = list(d["months"].items())
    w, h, left, top, plot_h = 820, 200, 20, 50, 110
    peak = max((c for _, c in months), default=1) or 1
    step = (w - 2 * left) / max(len(months), 1)
    body = f'<text x="{w - 20}" y="32" class="m" text-anchor="end">{sum(c for _, c in months):,} contributions · {len(months)} months</text>'
    for i, (month, count) in enumerate(months):
        bh = max(2, plot_h * count / peak) if count else 2
        x = left + i * step
        body += (f'<rect x="{x + 1:.1f}" y="{top + plot_h - bh:.1f}" width="{max(step - 2, 1):.1f}" height="{bh:.1f}" rx="2" '
                 f'fill="{t["bar"] if count else t["track"]}"><title>{month}: {count}</title></rect>')
        if month.endswith("-01") or i == 0:
            body += f'<text x="{x + 1:.1f}" y="{top + plot_h + 18}" class="m">{month[:4]}</text>'
    return frame(t, w, h, title, body)


def main():
    user, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    d = collect(user)
    cards = {
        "stats-dark.svg": stats_card(d, THEMES["dark"], "LIFETIME RECORD"),
        "stats-pink.svg": stats_card(d, THEMES["pink"], "♡ Lifetime Stats ♡"),
        "streak-dark.svg": streak_card(d, THEMES["dark"], "UNBROKEN"),
        "streak-pink.svg": streak_card(d, THEMES["pink"], "♡ Streak ♡"),
        "langs-dark.svg": langs_card(d, THEMES["dark"], "CURSED TECHNIQUES", LANG_COLORS),
        "langs-pink.svg": langs_card(d, THEMES["pink"], "♡ Languages ♡", LANG_COLORS_PINK),
        "history-dark.svg": history_card(d, THEMES["dark"], "BATTLE HISTORY"),
        "history-pink.svg": history_card(d, THEMES["pink"], "♬ Commit History ♬"),
    }
    for name, svg in cards.items():
        with open(os.path.join(out, name), "w", encoding="utf-8") as f:
            f.write(svg)
    print(json.dumps({k: v for k, v in d.items() if k not in ("months", "langs")}, default=str))


if __name__ == "__main__":
    main()
