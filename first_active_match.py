import argparse
import os
import xml.etree.ElementTree as ET
from datetime import datetime

import requests

from main import get_xml_text


def _load_env(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k and v and k not in os.environ:
                os.environ[k] = v


def _login(session: requests.Session) -> None:
    username = os.getenv("BB_USERNAME")
    security_code = os.getenv("BB_SECURITY_CODE")
    if not username or not security_code:
        raise SystemExit("Missing BB_USERNAME or BB_SECURITY_CODE in environment")
    resp = session.get(
        "http://bbapi.buzzerbeater.com/login.aspx",
        params={"login": username, "code": security_code},
    )
    resp.raise_for_status()


def _schedule_matches(session: requests.Session, team_id: int, season: int):
    resp = session.get(
        "http://bbapi.buzzerbeater.com/schedule.aspx",
        params={"teamid": team_id, "season": season},
    )
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    matches = []
    for match in root.findall(".//match"):
        mid = match.get("id")
        start = match.get("start")
        if not mid or not start:
            continue
        try:
            mid_int = int(mid)
        except ValueError:
            continue
        matches.append((mid_int, start))
    return matches


def _parse_team_name(match_xml: str, team_id: int) -> str | None:
    root = ET.fromstring(match_xml)
    for side in ("HomeTeam", "AwayTeam"):
        team = root.find(side)
        if team is None:
            continue
        tid = team.findtext("ID")
        if tid and tid.isdigit() and int(tid) == team_id:
            return team.findtext("Name")
    return None


def _sort_key(start: str):
    # Example format: ISO 8601 UTC timestamp (e.g., YYYY-MM-DDTHH:MM:SSZ)
    try:
        return datetime.fromisoformat(start.replace("Z", "+00:00"))
    except Exception:
        return start


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--teamid", type=int, required=True)
    parser.add_argument("--season", type=int, required=True)
    args = parser.parse_args()

    _load_env()
    session = requests.Session()
    _login(session)

    matches = _schedule_matches(session, args.teamid, args.season)
    matches.sort(key=lambda m: _sort_key(m[1]))

    season_names = []
    for mid, start in matches:
        xml = get_xml_text(mid)
        name = _parse_team_name(xml, args.teamid)
        if name:
            season_names.append((mid, start, name))

    if not season_names:
        print("No matches found for team in that season.")
        return

    last_name = season_names[-1][2]
    first_match = next(m for m in season_names if m[2] == last_name)

    print(f"season: {args.season}")
    print(f"last_name_in_season: {last_name}")
    print(f"first_match_with_last_name: {first_match[0]}")
    print(f"first_match_start: {first_match[1]}")


if __name__ == "__main__":
    main()
