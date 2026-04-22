from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.build_star_schema import ensure_star_schema


STAR_SCHEMA_DIR = ensure_star_schema()


def _read_csv(name: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    return pd.read_csv(STAR_SCHEMA_DIR / name, parse_dates=parse_dates)


def load_tables() -> dict[str, pd.DataFrame]:
    return {
        "dim_date": _read_csv("dim_date.csv", parse_dates=["date"]),
        "dim_team": _read_csv("dim_team.csv"),
        "dim_game": _read_csv("dim_game.csv", parse_dates=["game_datetime"]),
        "dim_player": _read_csv("dim_player.csv"),
        "fact_team_game": _read_csv("fact_team_game.csv", parse_dates=["game_datetime"]),
        "fact_player_game": _read_csv("fact_player_game.csv", parse_dates=["game_datetime"]),
    }


def load_schema_summary() -> dict:
    summary_path = Path(STAR_SCHEMA_DIR) / "schema_summary.json"
    return json.loads(summary_path.read_text(encoding="utf-8"))
