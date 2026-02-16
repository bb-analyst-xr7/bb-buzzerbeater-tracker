import argparse
import contextlib
import io
import json
import math

from comments import Comments
from event import convert, FreeThrowEvent, ShotEvent
from event_types import ShotType
from main import parse_xml, get_xml_text


REGULATION_SECONDS = 2880
OVERTIME_SECONDS = 300
# Court image is 368px wide and baskets are at x=21 and x=347 (326px apart).
# Real basket-to-basket distance is 83.5 ft (94 ft court - 2 * 5.25 ft).
FT_PER_PX = 83.5 / 326


def _is_buzzerbeater_comment(comment: str) -> bool:
    # Exact English template: "A buzzerbeater for $player1$!"
    return comment.startswith("A buzzerbeater for ") and comment.endswith("!")


def _build_period_ends(max_clock: int) -> list[int]:
    # Fallback: 4 quarters (720s each) plus any number of 5-min OTs.
    quarter_end = 720
    period_ends = [
        quarter_end * i for i in range(1, 5) if quarter_end * i <= max_clock
    ]
    if max_clock > REGULATION_SECONDS:
        extra = max_clock - REGULATION_SECONDS
        ot_count = (extra + OVERTIME_SECONDS - 1) // OVERTIME_SECONDS
        period_ends += [
            REGULATION_SECONDS + OVERTIME_SECONDS * i
            for i in range(1, ot_count + 1)
        ]
    if not period_ends:
        period_ends = [REGULATION_SECONDS]
    return period_ends


def _period_ends_from_events(events) -> list[int]:
    # Prefer explicit "End of period." markers when available (OT ends are offset in reports).
    ends = sorted(
        {
            ev.gameclock.clock
            for ev in events
            if (ev.comment or "") == "End of period."
        }
    )
    return ends


def _period_label_from_end(end: int, period_ends: list[int]) -> str:
    if end in period_ends:
        idx = period_ends.index(end) + 1
        if idx <= 4:
            return f"Q{idx}"
        return f"OT{idx - 4}"
    return _period_label(end)


def _matching_period_end(clock: int, period_ends: list[int]) -> int | None:
    for end in period_ends:
        if end - 5 <= clock <= end:
            return end
    return None


def _period_label(clock: int) -> str:
    if clock <= REGULATION_SECONDS:
        quarter = (clock + 719) // 720
        quarter = max(1, min(4, quarter))
        return f"Q{quarter}"
    ot_index = (clock - REGULATION_SECONDS + OVERTIME_SECONDS - 1) // OVERTIME_SECONDS
    return f"OT{ot_index}"


def find_buzzerbeaters(matchid: int):
    text = get_xml_text(matchid)
    # Suppress debug chatter from parse_report when __debug__ is True.
    with contextlib.redirect_stdout(io.StringIO()):
        events, ht, at = parse_xml(text)

    comments = Comments()
    # Populate comments and player objects for all events so convert() can work.
    for ev in events:
        with contextlib.redirect_stdout(io.StringIO()):
            ev.comment = comments.get_comment(ev, [ht, at])
    baseevents = convert(events)
    score_map = _score_snapshots(baseevents)
    hits = []
    max_clock = max((ev.gameclock.clock for ev in events), default=REGULATION_SECONDS)
    period_ends = _period_ends_from_events(events)
    if not period_ends:
        period_ends = _build_period_ends(max_clock)
    for ev in events:
        end = _matching_period_end(ev.gameclock.clock, period_ends)
        if end is None:
            continue
        if _is_buzzerbeater_comment(ev.comment):
            ev.period = _period_label_from_end(end, period_ends)
            _attach_scoring_details(ev, baseevents, score_map, end)
            hits.append(ev)

    return hits, ht, at


def _shot_distance(shot_event: ShotEvent) -> float | None:
    if shot_event.shot_pos is None:
        return None
    if shot_event.att_team == 0:
        basket_x, basket_y = 347, 96
    else:
        basket_x, basket_y = 21, 96
    dx = shot_event.shot_pos.x - basket_x
    dy = shot_event.shot_pos.y - basket_y
    return math.sqrt(dx * dx + dy * dy)


def _shot_distance_ft(shot_event: ShotEvent) -> float | None:
    dist_px = _shot_distance(shot_event)
    if dist_px is None:
        return None
    return dist_px * FT_PER_PX


def _attach_scoring_details(ev, baseevents, score_map, end: int) -> None:
    window_start = end - 5
    last_shot = None
    last_ft = None
    for be in baseevents:
        if be.gameclock < window_start or be.gameclock > end:
            continue
        if isinstance(be, ShotEvent):
            if be.att_team == ev.team and be.has_scored():
                last_shot = be
        elif isinstance(be, FreeThrowEvent):
            if be.att_team == ev.team and be.has_scored():
                last_ft = be

    chosen = last_shot if last_shot is not None else last_ft
    if chosen is None:
        ev.linked_event_kind = None
        return

    if isinstance(chosen, ShotEvent):
        ev.linked_event_kind = "shot"
        ev.shot_type = str(chosen.shot_type)
        ev.shot_type_label = ShotType(chosen.shot_type).name if chosen.shot_type else None
        ev.shot_result = str(chosen.shot_result)
        ev.free_throw_type = None
        ev.shot_x = chosen.shot_pos.x
        ev.shot_y = chosen.shot_pos.y
        ev.shot_distance = _shot_distance(chosen)
        ev.shot_distance_ft = _shot_distance_ft(chosen)
    else:
        ev.linked_event_kind = "free_throw"
        ev.shot_type = None
        ev.shot_type_label = None
        ev.shot_result = str(chosen.shot_result)
        ev.free_throw_type = str(chosen.free_throw_type)
        ev.shot_x = None
        ev.shot_y = None
        ev.shot_distance = None
        ev.shot_distance_ft = None

    # Attach score snapshot if available
    snap = score_map.get(chosen)
    if snap:
        before, after = snap
        ev.score_before_home = before[0]
        ev.score_before_away = before[1]
        ev.score_after_home = after[0]
        ev.score_after_away = after[1]


def _score_snapshots(baseevents):
    scores = [0, 0]
    snapshots = {}
    for be in baseevents:
        if isinstance(be, ShotEvent) and be.has_scored():
            pts = 3 if be.is_3pt() else 2
            before = (scores[0], scores[1])
            scores[be.att_team] += pts
            after = (scores[0], scores[1])
            snapshots[be] = (before, after)
        elif isinstance(be, FreeThrowEvent) and be.has_scored():
            before = (scores[0], scores[1])
            scores[be.att_team] += 1
            after = (scores[0], scores[1])
            snapshots[be] = (before, after)
    return snapshots


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matchid", type=int, required=True, help="Match ID")
    parser.add_argument(
        "--json", action="store_true", help="Print results as JSON"
    )
    parser.add_argument(
        "--details", action="store_true", help="Show linked scoring details"
    )
    args = parser.parse_args()

    hits, ht, at = find_buzzerbeaters(args.matchid)

    if args.json:
        payload = []
        for ev in hits:
            payload.append(
                {
                    "matchid": args.matchid,
                    "team": ht.name if ev.team == 0 else at.name,
                    "team_index": ev.team,
                    "event_type": ev.type,
                    "result": ev.result,
                    "variation": ev.variation,
                    "gameclock": ev.gameclock.clock,
                    "realclock": ev.realclock,
                    "data": ev.data,
                }
            )
        print(json.dumps(payload, indent=2))
    else:
        print(f"buzzerbeaters: {len(hits)}")
        for ev in hits:
            team_name = ht.name if ev.team == 0 else at.name
            period = getattr(ev, "period", None) or _period_label(ev.gameclock.clock)
            comment = ev.comment or ""
            line = f"- {team_name} {period} {comment}"
            if args.details:
                kind = getattr(ev, "linked_event_kind", None)
                if kind == "shot":
                    line += (
                        f" | shot_type={getattr(ev, 'shot_type', None)}"
                        f" shot_label={getattr(ev, 'shot_type_label', None)}"
                        f" shot_result={getattr(ev, 'shot_result', None)}"
                        f" pos=({getattr(ev, 'shot_x', None)},{getattr(ev, 'shot_y', None)})"
                        f" dist_px={getattr(ev, 'shot_distance', None)}"
                        f" dist_ft={getattr(ev, 'shot_distance_ft', None)}"
                        f" score={getattr(ev, 'score_before_home', None)}-{getattr(ev, 'score_before_away', None)}"
                        f"→{getattr(ev, 'score_after_home', None)}-{getattr(ev, 'score_after_away', None)}"
                    )
                elif kind == "free_throw":
                    line += (
                        f" | free_throw_type={getattr(ev, 'free_throw_type', None)}"
                        f" shot_result={getattr(ev, 'shot_result', None)}"
                        f" score={getattr(ev, 'score_before_home', None)}-{getattr(ev, 'score_before_away', None)}"
                        f"→{getattr(ev, 'score_after_home', None)}-{getattr(ev, 'score_after_away', None)}"
                    )
                else:
                    line += " | scoring_event=unknown"
            print(line)


if __name__ == "__main__":
    main()
