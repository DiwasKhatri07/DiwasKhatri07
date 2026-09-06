#!/usr/bin/env python3
import json
import os
import re
import urllib.request
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
OWNER = os.environ.get("PROFILE_OWNER", "DiwasKhatri07")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
CODE_LINES = int(os.environ.get("CODE_LINES", "0"))


def request_json(url, method="GET", payload=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-metrics-workflow"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())


profile = request_json(f"https://api.github.com/users/{OWNER}")
repos = request_json(f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=updated")
repos = [repo for repo in repos if not repo.get("fork") and not repo.get("archived")]

query = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}}}"""
contrib_response = request_json(
    "https://api.github.com/graphql",
    method="POST",
    payload={"query": query, "variables": {"login": OWNER}},
)
calendar = contrib_response["data"]["user"]["contributionsCollection"]["contributionCalendar"]
days = [day for week in calendar["weeks"] for day in week["contributionDays"]]

stars = sum(repo.get("stargazers_count", 0) for repo in repos)
public_repos = profile.get("public_repos", 0)
followers = profile.get("followers", 0)
contributions = calendar.get("totalContributions", 0)
languages = {}
for repo in repos:
    language = repo.get("language")
    if language:
        languages[language] = languages.get(language, 0) + 1
top_languages = sorted(languages.items(), key=lambda item: (-item[1], item[0]))[:5]

BG, BORDER, TEXT, MUTED = "#0d1117", "#30363d", "#c9d1d9", "#8b949e"
BLUE, PURPLE, GREEN, ORANGE = "#58a6ff", "#bc8cff", "#3fb950", "#f0883e"

def esc(value):
    return escape(str(value), quote=True)

stats_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="300" viewBox="0 0 900 300" role="img" aria-labelledby="title desc">
<title id="title">{OWNER} GitHub statistics</title><desc id="desc">{public_repos} public repositories, {stars} stars, {followers} followers, {contributions} contributions.</desc>
<rect width="900" height="300" rx="18" fill="{BG}" stroke="{BORDER}"/>
<text x="34" y="42" fill="{BLUE}" font-family="monospace" font-size="21" font-weight="700">github --stats --auto</text>
<text x="34" y="70" fill="{MUTED}" font-family="monospace" font-size="14">{OWNER} · refreshed by GitHub Actions</text>
<line x1="34" y1="88" x2="866" y2="88" stroke="{BORDER}"/>
<g font-family="monospace" text-anchor="middle">
<text x="130" y="137" fill="{PURPLE}" font-size="28" font-weight="700">{public_repos}</text><text x="130" y="162" fill="{MUTED}" font-size="13">PUBLIC REPOS</text>
<text x="320" y="137" fill="{ORANGE}" font-size="28" font-weight="700">{stars}</text><text x="320" y="162" fill="{MUTED}" font-size="13">TOTAL STARS</text>
<text x="510" y="137" fill="{BLUE}" font-size="28" font-weight="700">{followers}</text><text x="510" y="162" fill="{MUTED}" font-size="13">FOLLOWERS</text>
<text x="700" y="137" fill="{GREEN}" font-size="28" font-weight="700">{contributions}</text><text x="700" y="162" fill="{MUTED}" font-size="13">CONTRIBUTIONS</text>
</g>
<text x="34" y="213" fill="{TEXT}" font-family="monospace" font-size="14">top languages</text>
<text x="34" y="244" fill="{BLUE}" font-family="monospace" font-size="16">{esc(' · '.join(f'{lang} ({count})' for lang, count in top_languages))}</text>
<text x="34" y="275" fill="{MUTED}" font-family="monospace" font-size="13">{CODE_LINES:,} measured code lines · refreshed daily</text>
</svg>'''
(ROOT / "github-stats.svg").write_text(stats_svg)

cell, gap, left, top = 11, 3, 42, 72
max_count = max((day["contributionCount"] for day in days), default=1)
def shade(count):
    if count == 0: return "#161b22"
    ratio = count / max_count
    return "#0e4429" if ratio < .25 else "#006d32" if ratio < .5 else "#26a641" if ratio < .75 else "#39d353"
rects = []
for index, day in enumerate(days):
    x = left + (index // 7) * (cell + gap)
    y = top + (index % 7) * (cell + gap)
    rects.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{shade(day["contributionCount"])}"><title>{esc(day["date"])}: {day["contributionCount"]} contributions</title></rect>')
contrib_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="220" viewBox="0 0 900 220" role="img" aria-labelledby="title desc">
<title id="title">{OWNER} contribution graph</title><desc id="desc">{contributions} contributions in the current GitHub contribution year.</desc>
<rect width="900" height="220" rx="18" fill="{BG}" stroke="{BORDER}"/>
<text x="34" y="38" fill="{PURPLE}" font-family="monospace" font-size="20" font-weight="700">contributions --year --auto</text>
<text x="34" y="60" fill="{MUTED}" font-family="monospace" font-size="13">{contributions} contributions · refreshed by GitHub Actions</text>
{''.join(rects)}
<text x="42" y="198" fill="{MUTED}" font-family="monospace" font-size="12">less</text><rect x="76" y="188" width="11" height="11" rx="2" fill="#161b22"/><rect x="92" y="188" width="11" height="11" rx="2" fill="#0e4429"/><rect x="108" y="188" width="11" height="11" rx="2" fill="#006d32"/><rect x="124" y="188" width="11" height="11" rx="2" fill="#26a641"/><rect x="140" y="188" width="11" height="11" rx="2" fill="#39d353"/><text x="160" y="198" fill="{MUTED}" font-family="monospace" font-size="12">more</text>
</svg>'''
(ROOT / "contributions.svg").write_text(contrib_svg)

readme = (ROOT / "README.md").read_text()
readme = re.sub(r"- \*\*\d+\*\* public repositories", f"- **{public_repos}** public repositories", readme)
readme = re.sub(r"- \*\*\d+\*\* total repository stars", f"- **{stars}** total repository stars", readme)
readme = re.sub(r"- \*\*\d+\*\* followers", f"- **{followers}** followers", readme)
readme = re.sub(r"- \*\*\d+\*\* measured physical lines", f"- **{CODE_LINES:,}** measured physical lines", readme)
readme = re.sub(r"- \*\*\d+\*\* contributions", f"- **{contributions}** contributions", readme)
(ROOT / "README.md").write_text(readme)
print(json.dumps({"repos": public_repos, "stars": stars, "followers": followers, "contributions": contributions, "code_lines": CODE_LINES}))
