# BB Insider

CLI tools for extracting match data and tracking buzzerbeaters.

## Setup (once)

1. Install `uv`: https://docs.astral.sh/uv/
2. Create a local `.env` in repo root:
   - `BB_USERNAME=...`
   - `BB_SECURITY_CODE=...`
3. Run commands from repo root with `uv run <command> ...`
   - Full options for any command: `uv run <command> --help`

## Main Tracking Workflow (3 commands)

These are the primary tracking commands for buzzerbeaters:

1. `bbinsider-buzzerbeaters`: check one match for buzzerbeaters (read-only, no DB writes).
2. `bbinsider-team-buzzerbeaters`: scan many matches and write/update `data/buzzerbeaters.db`.
3. `bbinsider-buzzerbeater-descriptions`: read `data/buzzerbeaters.db` and render text/summary output.

Dependency note:
- Command 3 depends on data created by command 2.
- Command 1 is an independent single-match check.

### `bbinsider-buzzerbeaters`
Detect buzzerbeaters in one match.

Useful flags:
- `--matchid` (required)
- `--details` (show linked shot/free-throw details)
- `--json`

Example (use your own match ID that has a buzzerbeater):

```bash
uv run bbinsider-buzzerbeaters --matchid <MATCH_ID_WITH_BUZZERBEATER> --details
```

### `bbinsider-team-buzzerbeaters`
Scan team matches and build/update buzzerbeater records in the local DB.

Option guide:
- `--teamid` (required): team to track.
- Season selection (pick one approach):
  - `--season <S>`: one season only.
  - `--seasons <S1,S2,...>`: explicit list.
  - `--season-from <A> --season-to <B>`: inclusive range.
- `--auto-first-season`: auto-detect the first season for the team name.
  - With no season flags, scans detected-first-season through current season.
  - With `--season-to`, sets the start from detected first season.
- `--from-first-active`: for the first scanned season, start from the team's first active match instead of all completed matches.
- `--db <PATH>`: target SQLite database path (default `data/buzzerbeaters.db`).
- `--tui`: show Rich progress UI while scanning.

Example (multi-season tracking):

```bash
uv run bbinsider-team-buzzerbeaters \
  --teamid <TEAM_ID> \
  --from-first-active \
  --auto-first-season \
  --season-to <SEASON>
```

Example (explicit range):

```bash
uv run bbinsider-team-buzzerbeaters \
  --teamid <TEAM_ID> \
  --season-from <SEASON_FROM> \
  --season-to <SEASON_TO>
```

### `bbinsider-buzzerbeater-descriptions`
Query the DB and render human-readable buzzerbeater lines and summaries.

Option guide:
- Data source:
  - `--db <PATH>` (default `data/buzzerbeaters.db`)
- Filters:
  - `--teamid`, `--opponent-id`, `--matchid`, `--player-id`
- Output mode:
  - `--verbosity 0`: tabular rows.
  - `--columns "col1,col2,..."`: columns used with `--verbosity 0`.
  - `--verbosity 1` or `--verbosity 2`: descriptive text output.
- Summary controls:
  - `--summary`: append aggregate breakdowns.
  - `--top-players <N>`: top players count in summary.
- Content filters:
  - `--only-outcome-change`: only events that changed game state at the buzzer.
- Link formatting:
  - `--no-url`: remove forum tags/viewer links from text.
- Special report modes (return immediately with dedicated tables):
  - `--multi-buzzer-games`
  - `--multi-player-games`

Example:

```bash
uv run bbinsider-buzzerbeater-descriptions --teamid <TEAM_ID> --summary
```

Example (compact table export):

```bash
uv run bbinsider-buzzerbeater-descriptions \
  --teamid <TEAM_ID> \
  --verbosity 0 \
  --columns "match_id,player_id,game_clock,period"
```

## Additional Commands

### `bbinsider`
Parse a single match and print stats/events or export JSON.

Useful flags:
- `--matchid` (required)
- `--print-events`
- `--print-stats`
- `--verify`
- `--out` (default: `output/reports/<matchid>.json`)

```bash
uv run bbinsider --matchid <MATCH_ID> --print-stats --print-events
```

### `bbinsider-team-info`
Fetch team metadata and first-season estimate.

```bash
uv run bbinsider-team-info --teamid <TEAM_ID>
```

### `bbinsider-team-shot-distance-hist`
Generate 2PT/3PT distance histograms for recent team matches.

Useful flags:
- `--teamid` (required)
- `--season` (optional season override)
- `--count` (number of most recent games)
- `--bin-width`
- `--out`

```bash
uv run bbinsider-team-shot-distance-hist --teamid <TEAM_ID> --count 20
```

### `bbinsider-shotchart`
Generate a shot chart image for a shot event type code.

Useful flags:
- positional `event_type` (integer code)
- `--out`

```bash
uv run bbinsider-shotchart <SHOT_EVENT_TYPE> --out output/charts/shot_<SHOT_EVENT_TYPE>.png
```

## Outputs

- Match XML cache: `matches/report_<matchid>.xml`
- Buzzerbeater DB: `data/buzzerbeaters.db`
- JSON reports: `output/reports/`
- Charts and other generated files: `output/`

## Privacy

- Keep `.env` local.
- Do not commit private exports/scrapes.
