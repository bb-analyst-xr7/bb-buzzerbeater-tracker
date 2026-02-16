import argparse
import os
import re
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup


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


def get_teaminfo(session: requests.Session, team_id: int) -> dict:
    resp = session.get(
        "http://bbapi.buzzerbeater.com/teaminfo.aspx", params={"teamid": team_id}
    )
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    team_elem = root.find(".//team")
    if team_elem is None:
        raise RuntimeError("teaminfo: missing team element")
    team_name = team_elem.findtext("teamName") or ""
    short_name = team_elem.findtext("shortName") or ""
    league_elem = team_elem.find("league")
    country_elem = team_elem.find("country")
    bot_team = team_elem.find("botTeam") is not None
    return {
        "team_id": team_id,
        "team_name": team_name,
        "short_name": short_name,
        "league_id": int(league_elem.get("id")) if league_elem is not None else None,
        "league_name": league_elem.text.strip() if league_elem is not None and league_elem.text else None,
        "country_id": int(country_elem.get("id")) if country_elem is not None else None,
        "country_name": country_elem.text.strip() if country_elem is not None and country_elem.text else None,
        "is_bot": bot_team,
    }


def get_team_history_from_webpage(session: requests.Session, team_id: int) -> list[dict]:
    url = f"https://buzzerbeater.com/team/{team_id}/history.aspx"
    resp = session.get(url)
    resp.raise_for_status()

    season_any_pattern = re.compile(
        r"In season (\d+),\s*(.+?)\s+(?:were|was|made|won|lost|played|finished|qualified).*",
        re.IGNORECASE,
    )

    soup = BeautifulSoup(resp.text, "html.parser")
    spans = soup.find_all("span")

    history_entries = []
    for span in spans:
        text = span.get_text(" ", strip=True)
        if "In season" not in text:
            continue
        match = season_any_pattern.search(text)
        if not match:
            continue
        season = int(match.group(1))
        team_name = match.group(2).strip()
        style = span.get("style") or ""
        is_muted = "color: gray" in style.lower()
        history_entries.append(
            {
                "season": season,
                "team_name": team_name,
                "league_name": None,
                "is_muted": is_muted,
            }
        )

    history_entries.sort(key=lambda x: x["season"], reverse=True)
    return history_entries


def first_season(history_entries: list[dict], current_team_name: str | None = None) -> int | None:
    if not history_entries:
        return None
    non_muted = [e for e in history_entries if not e.get("is_muted")]
    if non_muted:
        return min(entry["season"] for entry in non_muted)
    if current_team_name:
        current_name_entries = [
            entry for entry in history_entries if entry.get("team_name") == current_team_name
        ]
        if current_name_entries:
            return min(entry["season"] for entry in current_name_entries)
    return min(entry["season"] for entry in history_entries)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--teamid", type=int, required=True)
    args = parser.parse_args()

    _load_env()
    session = requests.Session()
    _login(session)

    info = get_teaminfo(session, args.teamid)
    history = get_team_history_from_webpage(session, args.teamid)
    first = first_season(history, info["team_name"])

    print(f"team_id: {info['team_id']}")
    print(f"team_name: {info['team_name']}")
    print(f"short_name: {info['short_name']}")
    print(f"is_bot: {info['is_bot']}")
    if first is not None:
        print(f"first_season: {first}")
    else:
        print("first_season: unknown")


if __name__ == "__main__":
    main()
