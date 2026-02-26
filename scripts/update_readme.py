#!/usr/bin/env python3
"""Fetch LeetCode stats and update README.md with live data."""

import json
import os
import re
import ssl
import urllib.request

USERNAME = "suresh-ixe"
README_PATH = "README.md"
LEETCODE_API = "https://leetcode.com/graphql"

QUERY = """
{
  matchedUser(username: "%s") {
    submitStatsGlobal {
      acSubmissionNum { difficulty count }
    }
    languageProblemCount { languageName problemsSolved }
    badges { displayName }
  }
  allQuestionsCount { difficulty count }
}
""" % USERNAME


def fetch_leetcode_data():
    payload = json.dumps({"query": QUERY}).encode("utf-8")
    req = urllib.request.Request(
        LEETCODE_API,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com",
            "User-Agent": "Mozilla/5.0",
        },
    )
    ctx = ssl.create_default_context()
    if os.environ.get("PYTHONHTTPSVERIFY", "1") == "0":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return json.loads(resp.read().decode())["data"]
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return json.loads(resp.read().decode())["data"]


def build_stats_table(data):
    solved_map = {
        item["difficulty"]: item["count"]
        for item in data["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]
    }
    total_map = {
        item["difficulty"]: item["count"]
        for item in data["allQuestionsCount"]
    }

    rows = []
    for diff, color in [("Easy", "brightgreen"), ("Medium", "orange"), ("Hard", "red")]:
        solved = solved_map.get(diff, 0)
        total = total_map.get(diff, 0)
        pct = f"{solved / total * 100:.2f}%" if total else "0%"
        rows.append(f"| **{diff}**   | {solved}    | {total}  | {pct}   |")

    all_solved = solved_map.get("All", 0)
    all_total = total_map.get("All", 0)
    all_pct = f"**{all_solved / all_total * 100:.2f}%**" if all_total else "0%"
    rows.append(f"| **Total**  | **{all_solved}**| {all_total}  | {all_pct} |")

    header = (
        "| Difficulty | Solved | Total | Progress |\n"
        "|:----------:|:------:|:-----:|:--------:|"
    )
    return header + "\n" + "\n".join(rows)


def build_languages_table(data):
    langs = sorted(
        data["matchedUser"]["languageProblemCount"],
        key=lambda x: x["problemsSolved"],
        reverse=True,
    )
    header = (
        "| Language   | Problems Solved |\n"
        "|:----------:|:---------------:|"
    )
    rows = [f"| {l['languageName']:<10} | {l['problemsSolved']:<15} |" for l in langs]
    return header + "\n" + "\n".join(rows)


def build_badges_section(data):
    badges = data["matchedUser"]["badges"]
    streak_badges = []
    challenge_badges = []

    for b in badges:
        name = b["displayName"]
        if "Days Badge" in name:
            streak_badges.append(name)
        elif "LeetCoding Challenge" in name:
            challenge_badges.append(name)

    lines = [f"- **{b}**" for b in streak_badges]
    if challenge_badges:
        lines.append(f"- Monthly LeetCoding Challenges: {', '.join(challenge_badges)}")
    return "\n".join(lines)


def replace_section(content, marker, replacement):
    pattern = re.compile(
        rf"(<!-- {marker}_START -->\n).*?(<!-- {marker}_END -->)",
        re.DOTALL,
    )
    return pattern.sub(rf"\1{replacement}\n\2", content)


def main():
    print(f"Fetching LeetCode data for {USERNAME}...")
    data = fetch_leetcode_data()

    with open(README_PATH, "r") as f:
        readme = f.read()

    readme = replace_section(readme, "LEETCODE_STATS", build_stats_table(data))
    readme = replace_section(readme, "LEETCODE_LANGUAGES", build_languages_table(data))
    readme = replace_section(readme, "LEETCODE_BADGES", build_badges_section(data))

    with open(README_PATH, "w") as f:
        f.write(readme)

    print("README.md updated successfully.")


if __name__ == "__main__":
    main()
