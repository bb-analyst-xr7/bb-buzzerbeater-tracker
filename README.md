# BB Insider

CLI utilities for BuzzerBeater match parsing, buzzerbeater detection, and team-level analysis.

## Requirements

- Python 3.10+
- `uv` (recommended): https://docs.astral.sh/uv/

## Quick Start (uv)

1. Install dependencies:
   - `uv sync`
2. Create a local `.env` file with:
   - `BB_USERNAME=...`
   - `BB_SECURITY_CODE=...`
3. Run commands with:
   - `uv run <command> ...`

Example:

```bash
uv run bbinsider --matchid 123786926 --print-stats --print-events
```

## Suggested First-Run Order

1. Parse one match and inspect output:
   - `uv run bbinsider --matchid 123786926 --print-stats --print-events`
2. Detect buzzerbeaters for a specific match:
   - `uv run bbinsider-buzzerbeaters --matchid 123786926 --details`
3. Check team metadata and first season hint:
   - `uv run bbinsider-team-info --teamid <TEAM_ID>`
4. Build team buzzerbeater history across seasons:
   - `uv run bbinsider-team-buzzerbeaters --teamid <TEAM_ID> --from-first-active --auto-first-season --season-to <SEASON>`
5. Generate description text from the DB:
   - `uv run bbinsider-buzzerbeater-descriptions --teamid <TEAM_ID> --summary`
6. Optional visual analysis:
   - `uv run bbinsider-shotchart <MATCH_ID> --out output/charts/shot_<MATCH_ID>.png`
   - `uv run bbinsider-team-shot-distance-hist --teamid <TEAM_ID> --count 20`

## Available Commands

- `bbinsider` - main match parser/output command.
- `bbinsider-shotchart` - generate a shot chart image from a match.
- `bbinsider-buzzerbeaters` - detect buzzerbeaters for a match and store/query details.
- `bbinsider-team-info` - fetch team metadata and first season estimate.
- `bbinsider-team-buzzerbeaters` - scan team matches across seasons for buzzerbeaters.
- `bbinsider-team-shot-distance-hist` - build team shot-distance histograms.
- `bbinsider-buzzerbeater-descriptions` - render text descriptions from buzzerbeater DB rows.

## Notes

- Runtime output and local data are written under ignored paths (for example `output/` and `data/`).
- Do not commit `.env` or any private exports/scrapes.
