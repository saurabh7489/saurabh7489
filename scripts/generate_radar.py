import os
import requests
import math
from collections import defaultdict
from datetime import datetime


USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
    "X-GitHub-Api-Version": "2026-03-10"
}


def github(url, params=None):
    response = requests.get(
        url,
        headers=HEADERS,
        params=params
    )

    response.raise_for_status()
    return response.json()


# --------------------------------------------------
# GET ALL PUBLIC REPOSITORIES
# --------------------------------------------------

repos = []

page = 1

while True:

    data = github(
        f"https://api.github.com/users/{USERNAME}/repos",
        {
            "per_page": 100,
            "page": page,
            "sort": "updated"
        }
    )

    if not data:
        break

    repos.extend(data)
    page += 1


# Ignore forks
repos = [
    repo for repo in repos
    if not repo["fork"]
]


# --------------------------------------------------
# COLLECT LANGUAGE DATA
# --------------------------------------------------

languages = defaultdict(int)

for repo in repos:

    try:

        data = github(
            f"https://api.github.com/repos/"
            f"{USERNAME}/{repo['name']}/languages"
        )

        for language, bytes_count in data.items():
            languages[language] += bytes_count

    except Exception:
        pass


# --------------------------------------------------
# LANGUAGE PERCENTAGES
# --------------------------------------------------

total_bytes = sum(languages.values())

language_percentages = {}

if total_bytes:

    for language, value in languages.items():

        language_percentages[language] = (
            value / total_bytes
        ) * 100


# --------------------------------------------------
# SKILL ANALYSIS
# --------------------------------------------------

skills = {}


def score_language(names):

    value = sum(
        language_percentages.get(name, 0)
        for name in names
    )

    return min(100, value * 3)


skills["JavaScript"] = score_language(
    ["JavaScript"]
)

skills["Python"] = score_language(
    ["Python"]
)

skills["Java"] = score_language(
    ["Java"]
)

skills["C++"] = score_language(
    ["C++"]
)

skills["HTML/CSS"] = score_language(
    ["HTML", "CSS"]
)


# --------------------------------------------------
# DETECT FRAMEWORKS / TOOLS
# --------------------------------------------------

repo_text = ""

for repo in repos:

    repo_text += " "

    repo_text += str(
        repo.get("name", "")
    )

    repo_text += " "

    repo_text += str(
        repo.get("description", "")
    )

    repo_text += " "

    repo_text += " ".join(
        repo.get("topics", [])
    )


repo_text = repo_text.lower()


# React
if "react" in repo_text:
    skills["React"] = 70
else:
    skills["React"] = 20


# Node.js
if "node" in repo_text or "nodejs" in repo_text:
    skills["Node.js"] = 70
else:
    skills["Node.js"] = 20


# Git/GitHub
if len(repos) > 0:
    skills["Git/GitHub"] = min(
        90,
        30 + len(repos) * 5
    )
else:
    skills["Git/GitHub"] = 10


# DSA
dsa_keywords = [
    "dsa",
    "data-structure",
    "algorithm",
    "leetcode",
    "binary-search",
    "recursion",
    "sorting",
    "tree",
    "graph"
]

dsa_hits = 0

for keyword in dsa_keywords:

    if keyword in repo_text:
        dsa_hits += 1


skills["DSA"] = min(
    90,
    25 + dsa_hits * 10
)


# --------------------------------------------------
# SELECT TOP 6 SKILLS
# --------------------------------------------------

skills = dict(
    sorted(
        skills.items(),
        key=lambda x: x[1],
        reverse=True
    )[:6]
)


# --------------------------------------------------
# LANGUAGE MIX
# --------------------------------------------------

top_languages = sorted(
    language_percentages.items(),
    key=lambda x: x[1],
    reverse=True
)[:6]


# --------------------------------------------------
# RADAR MATH
# --------------------------------------------------

def radar_points(
    values,
    cx,
    cy,
    radius
):

    points = []

    count = len(values)

    for i, value in enumerate(values):

        angle = (
            -math.pi / 2
            + (2 * math.pi * i / count)
        )

        r = radius * (value / 100)

        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)

        points.append(
            f"{x:.1f},{y:.1f}"
        )

    return " ".join(points)


def polygon(
    cx,
    cy,
    radius,
    count
):

    points = []

    for i in range(count):

        angle = (
            -math.pi / 2
            + (2 * math.pi * i / count)
        )

        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)

        points.append(
            f"{x:.1f},{y:.1f}"
        )

    return " ".join(points)


# --------------------------------------------------
# SVG
# --------------------------------------------------

WIDTH = 1100
HEIGHT = 600

LEFT_X = 280
RIGHT_X = 820
CENTER_Y = 310

RADIUS = 190


skill_names = list(skills.keys())
skill_values = list(skills.values())


language_names = [
    item[0]
    for item in top_languages
]

language_values = [
    item[1]
    for item in top_languages
]


# If fewer than 6 languages
while len(language_names) < 6:

    language_names.append("")

    language_values.append(0)


language_names = language_names[:6]
language_values = language_values[:6]


def radar_svg(
    cx,
    cy,
    radius,
    names,
    values
):

    count = len(names)

    svg = ""

    # Grid
    for level in [20, 40, 60, 80, 100]:

        svg += f"""
        <polygon
            points="{polygon(
                cx,
                cy,
                radius * level / 100,
                count
            )}"
            class="grid"/>
        """

    # Axis
    for i in range(count):

        angle = (
            -math.pi / 2
            + (2 * math.pi * i / count)
        )

        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)

        svg += f"""
        <line
            x1="{cx}"
            y1="{cy}"
            x2="{x:.1f}"
            y2="{y:.1f}"
            class="axis"/>
        """

    # Data
    points = radar_points(
        values,
        cx,
        cy,
        radius
    )

    svg += f"""
    <polygon
        points="{points}"
        class="radar"/>
    """

    # Points + labels
    for i, name in enumerate(names):

        angle = (
            -math.pi / 2
            + (2 * math.pi * i / count)
        )

        value = values[i]

        px = (
            cx
            + radius
            * (value / 100)
            * math.cos(angle)
        )

        py = (
            cy
            + radius
            * (value / 100)
            * math.sin(angle)
        )

        lx = (
            cx
            + (radius + 35)
            * math.cos(angle)
        )

        ly = (
            cy
            + (radius + 35)
            * math.sin(angle)
        )

        anchor = "middle"

        if lx < cx - 10:
            anchor = "end"

        elif lx > cx + 10:
            anchor = "start"

        svg += f"""
        <circle
            cx="{px:.1f}"
            cy="{py:.1f}"
            r="5"
            class="point"/>

        <text
            x="{lx:.1f}"
            y="{ly:.1f}"
            text-anchor="{anchor}"
            class="label">
            {name}
        </text>
        """

    return svg


left = radar_svg(
    LEFT_X,
    CENTER_Y,
    RADIUS,
    skill_names,
    skill_values
)

right = radar_svg(
    RIGHT_X,
    CENTER_Y,
    RADIUS,
    language_names,
    language_values
)


# --------------------------------------------------
# FINAL SVG
# --------------------------------------------------

svg = f"""
<svg
width="{WIDTH}"
height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}"
xmlns="http://www.w3.org/2000/svg">

<rect
width="100%"
height="100%"
fill="#0d1117"/>

<style>

.title {{
    fill: #ffffff;
    font-family: Arial;
    font-size: 20px;
    font-weight: bold;
}}

.label {{
    fill: #ffffff;
    font-family: Arial;
    font-size: 14px;
}}

.grid {{
    fill: none;
    stroke: #30363d;
    stroke-width: 1;
}}

.axis {{
    stroke: #30363d;
    stroke-width: 1;
}}

.radar {{
    fill: #238636;
    fill-opacity: .35;
    stroke: #39d353;
    stroke-width: 3;
}}

.point {{
    fill: #39d353;
}}

.divider {{
    stroke: #30363d;
    stroke-width: 1;
}}

</style>

<text
x="{LEFT_X}"
y="45"
text-anchor="middle"
class="title">
Skill Radar
</text>

{left}

<line
x1="550"
y1="0"
x2="550"
y2="{HEIGHT}"
class="divider"/>

<text
x="{RIGHT_X}"
y="45"
text-anchor="middle"
class="title">
Language Mix
</text>

{right}

</svg>
"""


# --------------------------------------------------
# WRITE FILE
# --------------------------------------------------

os.makedirs(
    "assets",
    exist_ok=True
)

with open(
    "assets/skill-radar.svg",
    "w",
    encoding="utf-8"
) as file:

    file.write(svg)


# --------------------------------------------------
# PRINT ANALYSIS
# --------------------------------------------------

print("\n===== GITHUB SKILL ANALYSIS =====\n")

print(f"Repositories analyzed: {len(repos)}")

print("\nLanguages:")

for language, percentage in sorted(
    language_percentages.items(),
    key=lambda x: x[1],
    reverse=True
):

    print(
        f"{language}: "
        f"{percentage:.1f}%"
    )


print("\nSkills:")

for skill, score in skills.items():

    print(
        f"{skill}: "
        f"{score:.0f}/100"
    )

print("\nRadar generated successfully.")