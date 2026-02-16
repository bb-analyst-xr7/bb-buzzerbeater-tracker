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
3. Run commands with either:
   - `uv run <command> ...`
   - `./uv_run.sh <command> ...`

Example:

```bash
./uv_run.sh bbinsider --matchid 123786926 --print-stats --print-events
```

## Available Commands

- `bbinsider` - main match parser/output command.
- `bbinsider-shotchart` - generate a shot chart image from a match.
- `bbinsider-buzzerbeaters` - detect buzzerbeaters for a match and store/query details.
- `bbinsider-team-info` - fetch team metadata and first season estimate.
- `bbinsider-team-buzzerbeaters` - scan team matches across seasons for buzzerbeaters.
- `bbinsider-debug-ot-buzzers` - debug overtime/period-end buzzer detection logic.
- `bbinsider-team-shot-distance-hist` - build team shot-distance histograms.
- `bbinsider-buzzerbeater-descriptions` - render text descriptions from buzzerbeater DB rows.

## Notes

- Runtime output and local data are written under ignored paths (for example `output/` and `data/`).
- Do not commit `.env` or any private exports/scrapes.
