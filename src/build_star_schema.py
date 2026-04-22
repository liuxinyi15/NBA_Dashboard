from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "archive"
OUTPUT_DIR = BASE_DIR / "data" / "star_schema"
TARGET_SEASON = "2025-26"
TARGET_SEASON_START = 2025


def season_from_datetime(series: pd.Series) -> pd.Series:
    dates = pd.to_datetime(series, errors="coerce")
    start_year = dates.dt.year.where(dates.dt.month >= 10, dates.dt.year - 1)
    return start_year.astype("Int64").astype(str) + "-" + (start_year + 1).astype("Int64").astype(str).str[-2:]


def _safe_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def _write_csv(df: pd.DataFrame, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_DIR / name, index=False)


def build_dim_team(team_stats: pd.DataFrame) -> pd.DataFrame:
    histories = pd.read_csv(RAW_DIR / "TeamHistories.csv")
    histories = _safe_numeric(histories, ["teamId", "seasonFounded", "seasonActiveTill"])
    histories = histories.sort_values(["teamId", "seasonActiveTill", "seasonFounded"])
    current_histories = histories[
        (histories["seasonFounded"] <= TARGET_SEASON_START)
        & (histories["seasonActiveTill"] >= TARGET_SEASON_START)
    ]
    current_histories = current_histories.loc[current_histories["league"] == "NBA"].drop_duplicates("teamId", keep="last")

    season_teams = (
        team_stats[["teamId", "teamCity", "teamName"]]
        .dropna()
        .drop_duplicates()
        .sort_values(["teamName", "teamCity"])
        .rename(
            columns={
                "teamId": "team_id",
                "teamCity": "team_city",
                "teamName": "team_name",
            }
        )
    )
    season_teams["team_full_name"] = season_teams["team_city"] + " " + season_teams["team_name"]

    current_histories = current_histories.rename(
        columns={
            "teamId": "team_id",
            "teamAbbrev": "team_abbrev",
            "seasonFounded": "season_founded",
            "seasonActiveTill": "season_active_till",
            "league": "league_name",
        }
    )[["team_id", "team_abbrev", "season_founded", "season_active_till", "league_name"]]

    dim_team = season_teams.merge(current_histories, on="team_id", how="inner")
    dim_team = dim_team.sort_values("team_full_name").reset_index(drop=True)
    return dim_team


def build_dim_date(team_stats: pd.DataFrame) -> pd.DataFrame:
    dates = pd.to_datetime(team_stats["gameDateTimeEst"], errors="coerce").dropna().dt.normalize()
    dim_date = pd.DataFrame({"date": dates.drop_duplicates().sort_values()})
    iso_calendar = dim_date["date"].dt.isocalendar()
    dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.month_name()
    dim_date["day"] = dim_date["date"].dt.day
    dim_date["weekday"] = dim_date["date"].dt.day_name()
    dim_date["iso_week"] = iso_calendar.week.astype(int)
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["is_weekend"] = dim_date["date"].dt.dayofweek >= 5
    dim_date["season"] = season_from_datetime(dim_date["date"])
    return dim_date


def build_dim_game(games: pd.DataFrame) -> pd.DataFrame:
    games = games.copy()
    games["game_datetime"] = pd.to_datetime(games["gameDateTimeEst"], errors="coerce")
    games["game_date"] = games["game_datetime"].dt.normalize()
    games["date_key"] = games["game_date"].dt.strftime("%Y%m%d").astype(int)
    games["score_margin"] = (pd.to_numeric(games["homeScore"], errors="coerce") - pd.to_numeric(games["awayScore"], errors="coerce")).abs()
    dim_game = games.rename(
        columns={
            "gameId": "game_id",
            "gameType": "game_type",
            "gameLabel": "game_label",
            "gameSubLabel": "game_sublabel",
            "seriesGameNumber": "series_game_number",
            "attendance": "attendance",
            "arenaName": "arena_name",
            "arenaCity": "arena_city",
            "arenaState": "arena_state",
            "hometeamId": "home_team_id",
            "awayteamId": "away_team_id",
            "homeScore": "home_score",
            "awayScore": "away_score",
        }
    )[
        [
            "game_id",
            "date_key",
            "game_datetime",
            "game_type",
            "game_label",
            "game_sublabel",
            "series_game_number",
            "attendance",
            "arena_name",
            "arena_city",
            "arena_state",
            "home_team_id",
            "away_team_id",
            "home_score",
            "away_score",
            "score_margin",
        ]
    ]
    return dim_game.sort_values("game_datetime").reset_index(drop=True)


def build_fact_team_game(team_stats: pd.DataFrame) -> pd.DataFrame:
    team_stats = team_stats.copy()
    team_stats["game_datetime"] = pd.to_datetime(team_stats["gameDateTimeEst"], errors="coerce")
    team_stats["game_date"] = team_stats["game_datetime"].dt.normalize()
    team_stats["date_key"] = team_stats["game_date"].dt.strftime("%Y%m%d").astype(int)
    numeric_columns = [
        "gameId",
        "teamId",
        "opponentTeamId",
        "home",
        "win",
        "teamScore",
        "opponentScore",
        "assists",
        "blocks",
        "steals",
        "fieldGoalsAttempted",
        "fieldGoalsMade",
        "fieldGoalsPercentage",
        "threePointersAttempted",
        "threePointersMade",
        "threePointersPercentage",
        "freeThrowsAttempted",
        "freeThrowsMade",
        "freeThrowsPercentage",
        "reboundsDefensive",
        "reboundsOffensive",
        "reboundsTotal",
        "foulsPersonal",
        "turnovers",
        "plusMinusPoints",
        "numMinutes",
        "q1Points",
        "q2Points",
        "q3Points",
        "q4Points",
        "benchPoints",
        "biggestLead",
        "biggestScoringRun",
        "leadChanges",
        "pointsFastBreak",
        "pointsFromTurnovers",
        "pointsInThePaint",
        "pointsSecondChance",
        "timesTied",
        "timeoutsRemaining",
        "seasonWins",
        "seasonLosses",
    ]
    team_stats = _safe_numeric(team_stats, numeric_columns)

    game_context = pd.read_csv(RAW_DIR / "Games.csv", usecols=["gameId", "gameDateTimeEst", "gameType"], low_memory=False)
    game_context = game_context.loc[season_from_datetime(game_context["gameDateTimeEst"]) == TARGET_SEASON]
    game_context = game_context.rename(columns={"gameType": "game_type"}).drop(columns=["gameDateTimeEst"]).drop_duplicates()
    game_context = _safe_numeric(game_context, ["gameId"])
    team_stats = team_stats.merge(game_context, on="gameId", how="left")

    advanced = pd.read_csv(RAW_DIR / "TeamStatisticsAdvanced.csv", low_memory=False)
    advanced = advanced.loc[season_from_datetime(advanced["gameDateTimeEst"]) == TARGET_SEASON].copy()
    advanced = _safe_numeric(
        advanced,
        [
            "gameId",
            "teamId",
            "defRating",
            "eDefRating",
            "eNetRating",
            "eOffRating",
            "ePace",
            "efgPct",
            "netRating",
            "offRating",
            "pace",
            "pie",
            "poss",
            "rebPct",
            "tmTovPct",
            "tsPct",
            "astPct",
        ],
    )
    advanced = advanced.rename(
        columns={
            "gameId": "gameId",
            "teamId": "teamId",
            "defRating": "def_rating",
            "eDefRating": "estimated_def_rating",
            "eNetRating": "estimated_net_rating",
            "eOffRating": "estimated_off_rating",
            "ePace": "estimated_pace",
            "efgPct": "effective_fg_pct",
            "netRating": "net_rating",
            "offRating": "off_rating",
            "pace": "pace",
            "pie": "pie",
            "poss": "possessions",
            "rebPct": "rebound_pct",
            "tmTovPct": "team_turnover_pct",
            "tsPct": "true_shooting_pct",
            "astPct": "assist_pct",
        }
    )[
        [
            "gameId",
            "teamId",
            "def_rating",
            "estimated_def_rating",
            "estimated_net_rating",
            "estimated_off_rating",
            "estimated_pace",
            "effective_fg_pct",
            "net_rating",
            "off_rating",
            "pace",
            "pie",
            "possessions",
            "rebound_pct",
            "team_turnover_pct",
            "true_shooting_pct",
            "assist_pct",
        ]
    ]

    four_factors = pd.read_csv(RAW_DIR / "TeamStatisticsFourFactors.csv", low_memory=False)
    four_factors = four_factors.loc[season_from_datetime(four_factors["gameDateTimeEst"]) == TARGET_SEASON].copy()
    four_factors = _safe_numeric(
        four_factors,
        ["gameId", "teamId", "efgPct", "ftaRate", "oppEfgPct", "oppFtaRate", "oppOrebPct", "oppTovPct", "orebPct", "tmTovPct"],
    )
    four_factors = four_factors.rename(
        columns={
            "efgPct": "four_factor_efg_pct",
            "ftaRate": "free_throw_rate",
            "oppEfgPct": "opp_effective_fg_pct",
            "oppFtaRate": "opp_free_throw_rate",
            "oppOrebPct": "opp_off_rebound_pct",
            "oppTovPct": "opp_turnover_pct",
            "orebPct": "off_rebound_pct",
            "tmTovPct": "four_factor_turnover_pct",
        }
    )[
        [
            "gameId",
            "teamId",
            "four_factor_efg_pct",
            "free_throw_rate",
            "opp_effective_fg_pct",
            "opp_free_throw_rate",
            "opp_off_rebound_pct",
            "opp_turnover_pct",
            "off_rebound_pct",
            "four_factor_turnover_pct",
        ]
    ]

    fact_team_game = team_stats.merge(advanced, on=["gameId", "teamId"], how="left").merge(
        four_factors, on=["gameId", "teamId"], how="left"
    )
    fact_team_game["team_game_key"] = fact_team_game["gameId"].astype("Int64").astype(str) + "_" + fact_team_game["teamId"].astype("Int64").astype(str)
    fact_team_game["win_pct_before_game"] = fact_team_game["seasonWins"] / (
        fact_team_game["seasonWins"] + fact_team_game["seasonLosses"]
    ).replace({0: np.nan})
    fact_team_game = fact_team_game.rename(
        columns={
            "gameId": "game_id",
            "teamId": "team_id",
            "opponentTeamId": "opponent_team_id",
            "home": "is_home",
            "win": "is_win",
            "gameType": "game_type",
            "teamCity": "team_city",
            "teamName": "team_name",
            "opponentTeamCity": "opponent_team_city",
            "opponentTeamName": "opponent_team_name",
            "teamScore": "team_score",
            "opponentScore": "opponent_score",
            "assists": "assists",
            "blocks": "blocks",
            "steals": "steals",
            "fieldGoalsAttempted": "field_goals_attempted",
            "fieldGoalsMade": "field_goals_made",
            "fieldGoalsPercentage": "field_goal_pct",
            "threePointersAttempted": "three_pointers_attempted",
            "threePointersMade": "three_pointers_made",
            "threePointersPercentage": "three_point_pct",
            "freeThrowsAttempted": "free_throws_attempted",
            "freeThrowsMade": "free_throws_made",
            "freeThrowsPercentage": "free_throw_pct",
            "reboundsDefensive": "defensive_rebounds",
            "reboundsOffensive": "offensive_rebounds",
            "reboundsTotal": "total_rebounds",
            "foulsPersonal": "personal_fouls",
            "turnovers": "turnovers",
            "plusMinusPoints": "plus_minus_points",
            "numMinutes": "minutes_played",
            "q1Points": "q1_points",
            "q2Points": "q2_points",
            "q3Points": "q3_points",
            "q4Points": "q4_points",
            "benchPoints": "bench_points",
            "biggestLead": "biggest_lead",
            "biggestScoringRun": "biggest_scoring_run",
            "leadChanges": "lead_changes",
            "pointsFastBreak": "points_fast_break",
            "pointsFromTurnovers": "points_from_turnovers",
            "pointsInThePaint": "points_in_the_paint",
            "pointsSecondChance": "points_second_chance",
            "timesTied": "times_tied",
            "timeoutsRemaining": "timeouts_remaining",
            "seasonWins": "season_wins_before_game",
            "seasonLosses": "season_losses_before_game",
        }
    )
    selected_columns = [
        "team_game_key",
        "game_id",
        "date_key",
        "game_datetime",
        "game_type",
        "team_id",
        "opponent_team_id",
        "is_home",
        "is_win",
        "team_city",
        "team_name",
        "opponent_team_city",
        "opponent_team_name",
        "team_score",
        "opponent_score",
        "assists",
        "blocks",
        "steals",
        "field_goals_attempted",
        "field_goals_made",
        "field_goal_pct",
        "three_pointers_attempted",
        "three_pointers_made",
        "three_point_pct",
        "free_throws_attempted",
        "free_throws_made",
        "free_throw_pct",
        "defensive_rebounds",
        "offensive_rebounds",
        "total_rebounds",
        "personal_fouls",
        "turnovers",
        "plus_minus_points",
        "minutes_played",
        "q1_points",
        "q2_points",
        "q3_points",
        "q4_points",
        "bench_points",
        "biggest_lead",
        "biggest_scoring_run",
        "lead_changes",
        "points_fast_break",
        "points_from_turnovers",
        "points_in_the_paint",
        "points_second_chance",
        "times_tied",
        "timeouts_remaining",
        "season_wins_before_game",
        "season_losses_before_game",
        "win_pct_before_game",
        "def_rating",
        "estimated_def_rating",
        "estimated_net_rating",
        "estimated_off_rating",
        "estimated_pace",
        "effective_fg_pct",
        "net_rating",
        "off_rating",
        "pace",
        "pie",
        "possessions",
        "rebound_pct",
        "team_turnover_pct",
        "true_shooting_pct",
        "assist_pct",
        "four_factor_efg_pct",
        "free_throw_rate",
        "opp_effective_fg_pct",
        "opp_free_throw_rate",
        "opp_off_rebound_pct",
        "opp_turnover_pct",
        "off_rebound_pct",
        "four_factor_turnover_pct",
    ]
    fact_team_game = fact_team_game[selected_columns].sort_values(["game_datetime", "team_id"]).reset_index(drop=True)
    return fact_team_game


def build_dim_player(players: pd.DataFrame, fact_player_game: pd.DataFrame) -> pd.DataFrame:
    dim_player = players.copy()
    dim_player = _safe_numeric(dim_player, ["personId", "heightInches", "bodyWeightLbs", "draftYear", "draftRound", "draftNumber"])
    dim_player = dim_player.rename(
        columns={
            "personId": "player_id",
            "firstName": "first_name",
            "lastName": "last_name",
            "birthDate": "birth_date",
            "school": "school",
            "country": "country",
            "heightInches": "height_inches",
            "bodyWeightLbs": "weight_lbs",
            "draftYear": "draft_year",
            "draftRound": "draft_round",
            "draftNumber": "draft_number",
        }
    )
    dim_player["player_full_name"] = (
        dim_player["first_name"].fillna("").str.strip() + " " + dim_player["last_name"].fillna("").str.strip()
    ).str.strip()
    dim_player["position_group"] = np.select(
        [dim_player["guard"] == 1, dim_player["forward"] == 1, dim_player["center"] == 1],
        ["Guard", "Forward", "Center"],
        default="Unknown",
    )
    active_player_ids = fact_player_game["player_id"].dropna().drop_duplicates()
    dim_player = dim_player.loc[dim_player["player_id"].isin(active_player_ids)].copy()
    selected_columns = [
        "player_id",
        "player_full_name",
        "first_name",
        "last_name",
        "birth_date",
        "school",
        "country",
        "height_inches",
        "weight_lbs",
        "position_group",
        "draft_year",
        "draft_round",
        "draft_number",
    ]
    return dim_player[selected_columns].sort_values("player_full_name").reset_index(drop=True)


def build_fact_player_game() -> pd.DataFrame:
    player_stats = pd.read_csv(RAW_DIR / "PlayerStatistics.csv", low_memory=False)
    player_stats["season"] = season_from_datetime(player_stats["gameDateTimeEst"])
    player_stats = player_stats.loc[player_stats["season"] == TARGET_SEASON].copy()
    player_stats["game_datetime"] = pd.to_datetime(player_stats["gameDateTimeEst"], errors="coerce")
    player_stats = player_stats.loc[player_stats["game_datetime"].notna()].copy()
    player_stats["date_key"] = player_stats["game_datetime"].dt.strftime("%Y%m%d").astype(int)
    player_stats = _safe_numeric(
        player_stats,
        [
            "personId",
            "gameId",
            "win",
            "home",
            "numMinutes",
            "points",
            "assists",
            "blocks",
            "steals",
            "fieldGoalsAttempted",
            "fieldGoalsMade",
            "fieldGoalsPercentage",
            "threePointersAttempted",
            "threePointersMade",
            "threePointersPercentage",
            "freeThrowsAttempted",
            "freeThrowsMade",
            "freeThrowsPercentage",
            "reboundsDefensive",
            "reboundsOffensive",
            "reboundsTotal",
            "foulsPersonal",
            "turnovers",
            "plusMinusPoints",
        ],
    )

    team_lookup = (
        pd.read_csv(RAW_DIR / "TeamStatistics.csv", usecols=["gameId", "teamId", "teamCity", "teamName", "opponentTeamId"], low_memory=False)
        .drop_duplicates()
        .rename(
            columns={
                "gameId": "gameId",
                "teamId": "team_id",
                "teamCity": "playerteamCity",
                "teamName": "playerteamName",
                "opponentTeamId": "opponent_team_id",
            }
        )
    )
    team_lookup = _safe_numeric(team_lookup, ["gameId", "team_id", "opponent_team_id"])
    player_stats = player_stats.merge(team_lookup, on=["gameId", "playerteamCity", "playerteamName"], how="left")

    advanced = pd.read_csv(RAW_DIR / "PlayerStatisticsAdvanced.csv", low_memory=False)
    advanced["season"] = season_from_datetime(advanced["gameDateTimeEst"])
    advanced = advanced.loc[advanced["season"] == TARGET_SEASON].copy()
    advanced = _safe_numeric(
        advanced,
        [
            "gameId",
            "personId",
            "netRating",
            "offRating",
            "defRating",
            "tsPct",
            "usgPct",
            "pace",
            "pie",
            "poss",
            "astPct",
            "rebPct",
        ],
    )
    advanced = advanced.rename(
        columns={
            "netRating": "net_rating",
            "offRating": "off_rating",
            "defRating": "def_rating",
            "tsPct": "true_shooting_pct",
            "usgPct": "usage_pct",
            "pace": "pace",
            "pie": "pie",
            "poss": "possessions",
            "astPct": "assist_pct",
            "rebPct": "rebound_pct",
        }
    )[
        [
            "gameId",
            "personId",
            "net_rating",
            "off_rating",
            "def_rating",
            "true_shooting_pct",
            "usage_pct",
            "pace",
            "pie",
            "possessions",
            "assist_pct",
            "rebound_pct",
        ]
    ]
    player_stats = player_stats.merge(advanced, on=["gameId", "personId"], how="left")

    fact_player_game = player_stats.rename(
        columns={
            "personId": "player_id",
            "gameId": "game_id",
            "playerteamCity": "team_city",
            "playerteamName": "team_name",
            "opponentteamCity": "opponent_team_city",
            "opponentteamName": "opponent_team_name",
            "gameType": "game_type",
            "gameLabel": "game_label",
            "gameSubLabel": "game_sublabel",
            "win": "is_win",
            "home": "is_home",
            "numMinutes": "minutes_played",
            "points": "points",
            "assists": "assists",
            "blocks": "blocks",
            "steals": "steals",
            "fieldGoalsAttempted": "field_goals_attempted",
            "fieldGoalsMade": "field_goals_made",
            "fieldGoalsPercentage": "field_goal_pct",
            "threePointersAttempted": "three_pointers_attempted",
            "threePointersMade": "three_pointers_made",
            "threePointersPercentage": "three_point_pct",
            "freeThrowsAttempted": "free_throws_attempted",
            "freeThrowsMade": "free_throws_made",
            "freeThrowsPercentage": "free_throw_pct",
            "reboundsDefensive": "defensive_rebounds",
            "reboundsOffensive": "offensive_rebounds",
            "reboundsTotal": "total_rebounds",
            "foulsPersonal": "personal_fouls",
            "turnovers": "turnovers",
            "plusMinusPoints": "plus_minus_points",
        }
    )
    fact_player_game["player_game_key"] = (
        fact_player_game["game_id"].astype("Int64").astype(str) + "_" + fact_player_game["player_id"].astype("Int64").astype(str)
    )
    selected_columns = [
        "player_game_key",
        "game_id",
        "date_key",
        "game_datetime",
        "game_type",
        "game_label",
        "game_sublabel",
        "player_id",
        "team_id",
        "opponent_team_id",
        "is_home",
        "is_win",
        "team_city",
        "team_name",
        "opponent_team_city",
        "opponent_team_name",
        "minutes_played",
        "points",
        "assists",
        "blocks",
        "steals",
        "field_goals_attempted",
        "field_goals_made",
        "field_goal_pct",
        "three_pointers_attempted",
        "three_pointers_made",
        "three_point_pct",
        "free_throws_attempted",
        "free_throws_made",
        "free_throw_pct",
        "defensive_rebounds",
        "offensive_rebounds",
        "total_rebounds",
        "personal_fouls",
        "turnovers",
        "plus_minus_points",
        "net_rating",
        "off_rating",
        "def_rating",
        "true_shooting_pct",
        "usage_pct",
        "pace",
        "pie",
        "possessions",
        "assist_pct",
        "rebound_pct",
    ]
    fact_player_game = fact_player_game[selected_columns].sort_values(["game_datetime", "team_id", "player_id"]).reset_index(drop=True)
    return fact_player_game


def build_schema(force: bool = False) -> None:
    required_outputs = [
        OUTPUT_DIR / "dim_date.csv",
        OUTPUT_DIR / "dim_team.csv",
        OUTPUT_DIR / "dim_game.csv",
        OUTPUT_DIR / "dim_player.csv",
        OUTPUT_DIR / "fact_team_game.csv",
        OUTPUT_DIR / "fact_player_game.csv",
        OUTPUT_DIR / "schema_summary.json",
    ]
    if not force and all(path.exists() for path in required_outputs):
        return

    games = pd.read_csv(RAW_DIR / "Games.csv", low_memory=False)
    games = games.loc[season_from_datetime(games["gameDateTimeEst"]) == TARGET_SEASON].copy()
    games = _safe_numeric(
        games,
        ["gameId", "hometeamId", "awayteamId", "homeScore", "awayScore", "attendance"],
    )

    team_stats = pd.read_csv(RAW_DIR / "TeamStatistics.csv", low_memory=False)
    team_stats["season"] = season_from_datetime(team_stats["gameDateTimeEst"])
    team_stats = team_stats.loc[team_stats["season"] == TARGET_SEASON].copy()

    dim_team = build_dim_team(team_stats)
    valid_team_ids = set(dim_team["team_id"].dropna().astype(int).tolist())

    games = games.loc[games["hometeamId"].isin(valid_team_ids) & games["awayteamId"].isin(valid_team_ids)].copy()
    team_stats = team_stats.loc[team_stats["teamId"].isin(valid_team_ids) & team_stats["opponentTeamId"].isin(valid_team_ids)].copy()

    fact_player_game = build_fact_player_game()
    fact_player_game = fact_player_game.loc[
        fact_player_game["team_id"].isin(valid_team_ids) & fact_player_game["opponent_team_id"].isin(valid_team_ids)
    ].copy()
    dim_player = build_dim_player(pd.read_csv(RAW_DIR / "Players.csv", low_memory=False), fact_player_game)
    dim_date = build_dim_date(team_stats)
    dim_game = build_dim_game(games)
    fact_team_game = build_fact_team_game(team_stats)

    _write_csv(dim_date, "dim_date.csv")
    _write_csv(dim_team, "dim_team.csv")
    _write_csv(dim_game, "dim_game.csv")
    _write_csv(dim_player, "dim_player.csv")
    _write_csv(fact_team_game, "fact_team_game.csv")
    _write_csv(fact_player_game, "fact_player_game.csv")

    summary = {
        "season": TARGET_SEASON,
        "tables": [
            {
                "name": "fact_team_game",
                "grain": "One row per team per game",
                "rows": int(len(fact_team_game)),
                "columns": list(fact_team_game.columns),
            },
            {
                "name": "fact_player_game",
                "grain": "One row per player per game",
                "rows": int(len(fact_player_game)),
                "columns": list(fact_player_game.columns),
            },
            {
                "name": "dim_team",
                "grain": "One row per active 2025-26 team",
                "rows": int(len(dim_team)),
                "columns": list(dim_team.columns),
            },
            {
                "name": "dim_player",
                "grain": "One row per player active in the 2025-26 season data",
                "rows": int(len(dim_player)),
                "columns": list(dim_player.columns),
            },
            {
                "name": "dim_game",
                "grain": "One row per game",
                "rows": int(len(dim_game)),
                "columns": list(dim_game.columns),
            },
            {
                "name": "dim_date",
                "grain": "One row per calendar date in the season",
                "rows": int(len(dim_date)),
                "columns": list(dim_date.columns),
            },
        ],
        "relationships": [
            "fact_team_game.date_key -> dim_date.date_key",
            "fact_team_game.team_id -> dim_team.team_id",
            "fact_team_game.opponent_team_id -> dim_team.team_id",
            "fact_team_game.game_id -> dim_game.game_id",
            "fact_player_game.date_key -> dim_date.date_key",
            "fact_player_game.team_id -> dim_team.team_id",
            "fact_player_game.opponent_team_id -> dim_team.team_id",
            "fact_player_game.player_id -> dim_player.player_id",
            "fact_player_game.game_id -> dim_game.game_id",
        ],
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "schema_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def ensure_star_schema(force: bool = False) -> Path:
    build_schema(force=force)
    return OUTPUT_DIR


if __name__ == "__main__":
    ensure_star_schema(force=True)
