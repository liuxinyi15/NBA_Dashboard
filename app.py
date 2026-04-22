from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.dashboard_data import load_tables


SEASON_LABEL = "2025-26"
ACCENT = "#D95D39"
SECONDARY = "#12355B"
BACKGROUND = "#F6F3EE"
TEAM_COLORS = px.colors.qualitative.Safe


st.set_page_config(
    page_title="NBA 2025-26 Dashboard",
    page_icon="🏀",
    layout="wide",
)


st.markdown(
    f"""
    <style>
        .stApp {{
            background:
                radial-gradient(circle at top right, rgba(217, 93, 57, 0.16), transparent 32%),
                radial-gradient(circle at top left, rgba(18, 53, 91, 0.12), transparent 28%),
                {BACKGROUND};
        }}
        .hero {{
            padding: 1.5rem 1.7rem;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(18,53,91,0.96), rgba(25,91,145,0.92));
            color: #F8F6F2;
            box-shadow: 0 20px 60px rgba(18,53,91,0.22);
            margin-bottom: 1.2rem;
        }}
        .hero h1 {{
            margin: 0;
            font-size: 2.6rem;
        }}
        .hero p {{
            margin: 0.35rem 0 0;
            max-width: 800px;
            font-size: 1rem;
        }}
        .metric-card {{
            background: rgba(255,255,255,0.75);
            border: 1px solid rgba(18,53,91,0.08);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            box-shadow: 0 10px 30px rgba(18,53,91,0.08);
        }}
        .metric-label {{
            color: #5B6270;
            font-size: 0.84rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        .metric-value {{
            color: {SECONDARY};
            font-size: 1.8rem;
            font-weight: 700;
            line-height: 1.2;
        }}
        .metric-note {{
            color: #4A5563;
            font-size: 0.88rem;
        }}
        .story-block {{
            background: rgba(255,255,255,0.78);
            border-left: 6px solid {ACCENT};
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 30px rgba(18,53,91,0.08);
            margin: 0.5rem 0 1rem 0;
        }}
        .story-kicker {{
            color: {ACCENT};
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }}
        .story-title {{
            color: {SECONDARY};
            font-size: 1.35rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }}
        .story-body {{
            color: #334155;
            font-size: 0.98rem;
            line-height: 1.6;
        }}
        .story-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 0.3rem 0 1rem 0;
        }}
        .story-chip {{
            background: rgba(255,255,255,0.78);
            border: 1px solid rgba(18,53,91,0.08);
            border-radius: 16px;
            padding: 0.9rem 1rem;
            box-shadow: 0 10px 30px rgba(18,53,91,0.06);
        }}
        .story-chip strong {{
            display: block;
            color: {SECONDARY};
            margin-bottom: 0.25rem;
        }}
        div[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(246,243,238,0.98));
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def get_data() -> dict[str, pd.DataFrame]:
    return load_tables()


def metric_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def story_block(kicker: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="story-block">
            <div class="story-kicker">{kicker}</div>
            <div class="story-title">{title}</div>
            <div class="story-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def story_grid(items: list[tuple[str, str]]) -> None:
    chips = "".join(
        f'<div class="story-chip"><strong>{title}</strong><span>{body}</span></div>' for title, body in items
    )
    st.markdown(f'<div class="story-grid">{chips}</div>', unsafe_allow_html=True)


def apply_chart_style(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.7)",
        font=dict(family="Georgia, Times New Roman, serif", color="#213547"),
        margin=dict(l=16, r=16, t=48, b=16),
        legend_title_text="",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(18,53,91,0.08)")
    return fig


def format_corr(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}"


def format_value(value: float, spec: str = ".1f", fallback: str = "—") -> str:
    if pd.isna(value):
        return fallback
    return format(value, spec)


def format_pct(value: float, fallback: str = "—") -> str:
    if pd.isna(value):
        return fallback
    return f"{value:.1%}"


tables = get_data()
dim_team = tables["dim_team"]
dim_player = tables["dim_player"]
fact_team_game = tables["fact_team_game"]
fact_player_game = tables["fact_player_game"]

fact_team_game["result_label"] = fact_team_game["is_win"].map({1: "Win", 0: "Loss"})
fact_team_game["home_away"] = fact_team_game["is_home"].map({1: "Home", 0: "Away"})

st.markdown(
    """
    <div class="hero">
        <h1>NBA 2025-26 Performance Dashboard</h1>
        <p>
            A regular-season dashboard focused on team quality, player roles, and the profiles behind winning records.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Team Explorer", "Player Explorer"],
)

regular_team_games = fact_team_game.loc[fact_team_game["game_type"] == "Regular Season"].copy()
regular_player_games = fact_player_game.loc[fact_player_game["game_type"] == "Regular Season"].copy()
filtered_team_games = regular_team_games if not regular_team_games.empty else fact_team_game.copy()
filtered_player_games = regular_player_games if not regular_player_games.empty else fact_player_game.copy()


if page == "Overview":
    story_game_threshold = 10
    team_summary = (
        filtered_team_games.groupby(["team_id", "team_city", "team_name"], as_index=False)
        .agg(
            games=("game_id", "nunique"),
            win_pct=("is_win", "mean"),
            off_rating=("off_rating", "mean"),
            def_rating=("def_rating", "mean"),
            net_rating=("net_rating", "mean"),
            pace=("pace", "mean"),
            efg_pct=("effective_fg_pct", "mean"),
        )
    )
    team_table = team_summary.query("games >= @story_game_threshold").copy()
    if team_table.empty:
        team_table = team_summary.copy()
    team_table["team_full_name"] = team_table["team_city"] + " " + team_table["team_name"]
    team_table = team_table.sort_values(["win_pct", "net_rating"], ascending=False)

    league_games = filtered_team_games["game_id"].nunique()
    league_teams = filtered_team_games["team_id"].nunique()
    active_players = filtered_player_games["player_id"].nunique()
    avg_score = filtered_team_games["team_score"].mean()
    avg_pace = filtered_team_games["pace"].mean()

    latest_date = filtered_team_games["game_datetime"].max()
    latest_note = f"Regular season through {latest_date:%Y-%m-%d}" if pd.notna(latest_date) else "No date available"

    top_team = team_table.head(1)
    top_team_label = (
        f"{top_team.iloc[0]['team_city']} {top_team.iloc[0]['team_name']}" if not top_team.empty else "N/A"
    )
    best_offense = team_table.sort_values("off_rating", ascending=False).iloc[0]
    best_defense = team_table.sort_values("def_rating", ascending=True).iloc[0]
    fastest_team = team_table.sort_values("pace", ascending=False).iloc[0]
    contender_table = team_table.head(8).copy()
    story_player_threshold = 20
    player_story = (
        filtered_player_games.groupby(["player_id", "team_id"], as_index=False)
        .agg(
            games=("game_id", "nunique"),
            points=("points", "mean"),
            assists=("assists", "mean"),
            rebounds=("total_rebounds", "mean"),
            true_shooting_pct=("true_shooting_pct", "mean"),
            usage_pct=("usage_pct", "mean"),
            net_rating=("net_rating", "mean"),
            minutes=("minutes_played", "mean"),
        )
        .query("games >= @story_player_threshold and minutes >= 15")
        .merge(dim_player[["player_id", "player_full_name"]], on="player_id", how="left")
        .merge(team_table[["team_id", "team_full_name", "win_pct"]], on="team_id", how="left")
    )
    contender_player_pool = player_story.loc[player_story["team_id"].isin(contender_table.head(6)["team_id"])].copy()
    win_efg_corr = team_table["win_pct"].corr(team_table["efg_pct"])
    win_def_corr = team_table["win_pct"].corr(-team_table["def_rating"])
    has_star_story = not contender_player_pool.empty
    if has_star_story:
        star_scorer = contender_player_pool.sort_values(["points", "true_shooting_pct"], ascending=False).iloc[0]
        star_connector = contender_player_pool.sort_values(["assists", "usage_pct"], ascending=False).iloc[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("Games", f"{league_games:,}", latest_note)
    with c2:
        metric_card("Teams", f"{league_teams}", "Distinct franchises in the current filter")
    with c3:
        metric_card("Players", f"{active_players:,}", "Players with at least one logged appearance")
    with c4:
        metric_card("Avg Team Score", format_value(avg_score), "Average points per team-game")
    with c5:
        metric_card("League Pace", format_value(avg_pace), f"Top record: {top_team_label}")

    story_block(
        "Overview",
        "A quick read of the season",
        (
            f"{top_team_label} has the best record in the current view ({format_pct(top_team.iloc[0]['win_pct'])}). "
            f"{best_offense['team_city']} {best_offense['team_name']} leads in offensive rating "
            f"({format_value(best_offense['off_rating'])}), and {best_defense['team_city']} {best_defense['team_name']} "
            f"has the best defense ({format_value(best_defense['def_rating'])}). "
            f"Win rate is more closely related to shooting efficiency ({format_corr(win_efg_corr)}) and defense "
            f"({format_corr(win_def_corr)}) than to pace, so fast teams like "
            f"{fastest_team['team_city']} {fastest_team['team_name']} are not automatically the best teams."
        ),
    )
    story_grid(
        [
            (
                "League level",
                f"Average scoring is {format_value(avg_score)} points per team-game.",
            ),
            (
                "Team level",
                "The top teams tend to be strong on both offense and defense.",
            ),
            (
                "Player level",
                "Star production matters most when it comes with efficiency.",
            ),
        ]
    )

    daily_summary = filtered_team_games.copy()
    daily_summary["game_date"] = daily_summary["game_datetime"].dt.normalize()
    daily_summary = (
        daily_summary.groupby("game_date", as_index=False)
        .agg(games=("game_id", "nunique"), avg_score=("team_score", "mean"), avg_pace=("pace", "mean"))
    )
    fig_daily = px.line(
        daily_summary,
        x="game_date",
        y=["games", "avg_score"],
        markers=True,
        color_discrete_sequence=[SECONDARY, ACCENT],
        title="Games and Scoring Over Time",
    )
    fig_daily.update_layout(yaxis_title="Value")
    fig_daily = apply_chart_style(fig_daily)

    fig_scatter = px.scatter(
        team_table,
        x="def_rating",
        y="off_rating",
        size="win_pct",
        color="net_rating",
        hover_name="team_full_name",
        color_continuous_scale="RdYlBu_r",
        title="Offense and Defense by Team",
        labels={"def_rating": "Defensive rating (lower is better)", "off_rating": "Offensive rating", "net_rating": "Net rating"},
    )
    fig_scatter.add_vline(x=team_table["def_rating"].mean(), line_dash="dash", line_color="rgba(18,53,91,0.35)")
    fig_scatter.add_hline(y=team_table["off_rating"].mean(), line_dash="dash", line_color="rgba(18,53,91,0.35)")
    fig_scatter.update_xaxes(autorange="reversed")
    for _, row in contender_table.head(5).iterrows():
        fig_scatter.add_annotation(
            x=row["def_rating"],
            y=row["off_rating"],
            text=row["team_name"],
            showarrow=False,
            yshift=12,
            font=dict(size=11, color="#102A43"),
            bgcolor="rgba(255,255,255,0.72)",
        )
    fig_scatter = apply_chart_style(fig_scatter)

    leaderboard = team_table.sort_values("off_rating", ascending=False).head(10)
    fig_offense = px.bar(
        leaderboard.sort_values("off_rating"),
        x="off_rating",
        y="team_full_name",
        orientation="h",
        color="win_pct",
        color_continuous_scale="Oranges",
        title="Top Offenses",
        labels={"off_rating": "Offensive rating", "team_full_name": ""},
    )
    fig_offense = apply_chart_style(fig_offense)

    if has_star_story:
        fig_stars = px.scatter(
            contender_player_pool,
            x="usage_pct",
            y="true_shooting_pct",
            size="points",
            color="team_full_name",
            hover_name="player_full_name",
            title="Usage and Efficiency for Key Players",
            labels={"usage_pct": "Usage rate", "true_shooting_pct": "True shooting %", "team_full_name": "Team"},
        )
        for _, row in contender_player_pool.sort_values("points", ascending=False).head(5).iterrows():
            fig_stars.add_annotation(
                x=row["usage_pct"],
                y=row["true_shooting_pct"],
                text=row["player_full_name"],
                showarrow=False,
                yshift=12,
                font=dict(size=10, color="#102A43"),
                bgcolor="rgba(255,255,255,0.72)",
            )
        fig_stars = apply_chart_style(fig_stars)

    col_a, col_b = st.columns([1.4, 1])
    with col_a:
        st.plotly_chart(fig_daily, width="stretch")
    with col_b:
        st.plotly_chart(fig_scatter, width="stretch")

    story_block(
        "What stands out",
        "The strongest teams are usually balanced teams",
        (
            f"Teams in the upper-left of the scatter combine strong offense with strong defense. "
            f"In this view, {top_team_label} has the clearest all-around profile, while "
            f"{best_offense['team_city']} {best_offense['team_name']} stands out for scoring efficiency."
        ),
    )
    st.plotly_chart(fig_offense, width="stretch")
    if has_star_story:
        st.plotly_chart(fig_stars, width="stretch")
        story_block(
            "Player view",
            "High volume matters more when it is efficient",
            (
                f"{star_scorer['player_full_name']} leads this group in scoring at "
                f"{star_scorer['points']:.1f} points per game, while {star_connector['player_full_name']} stands out as a creator "
                f"with {star_connector['assists']:.1f} assists per game. The chart is meant to show which players combine large roles with efficient output."
            ),
        )
    else:
        story_block(
            "Player view",
            "Not enough data for a useful player comparison.",
            "Try adding Regular Season or widening the filter."
        )

    standings = team_table.sort_values(["win_pct", "net_rating"], ascending=False).copy()
    standings["win_pct"] = standings["win_pct"].map(lambda value: f"{value:.1%}")
    standings["off_rating"] = standings["off_rating"].map(lambda value: f"{value:.1f}")
    standings["def_rating"] = standings["def_rating"].map(lambda value: f"{value:.1f}")
    standings["net_rating"] = standings["net_rating"].map(lambda value: f"{value:.1f}")
    standings["pace"] = standings["pace"].map(lambda value: f"{value:.1f}")
    standings["efg_pct"] = standings["efg_pct"].map(lambda value: f"{value:.1%}")
    st.dataframe(
        standings[
            ["team_full_name", "games", "win_pct", "off_rating", "def_rating", "net_rating", "pace", "efg_pct"]
        ],
        width="stretch",
        hide_index=True,
    )

    with st.expander("Data model", expanded=False):
        st.markdown(
            f"""
            This dashboard is built on an explicit star schema for the **{SEASON_LABEL}** season.

            Fact tables:
            - `fact_team_game`: one row per team per game
            - `fact_player_game`: one row per player per game

            Dimensions:
            - `dim_date`
            - `dim_team`
            - `dim_game`
            - `dim_player`
            """
        )


elif page == "Team Explorer":
    st.markdown(
        "Use this page to look more closely at how one team wins games."
    )
    team_options = dim_team["team_full_name"].sort_values().tolist()
    selected_team = st.selectbox("Choose a team", team_options)
    team_row = dim_team.loc[dim_team["team_full_name"] == selected_team].iloc[0]
    team_games = filtered_team_games.loc[filtered_team_games["team_id"] == team_row["team_id"]].copy()
    team_games = team_games.sort_values("game_datetime")

    wins = int(team_games["is_win"].sum())
    losses = int(len(team_games) - wins)
    avg_net = team_games["net_rating"].mean()
    avg_off = team_games["off_rating"].mean()
    avg_def = team_games["def_rating"].mean()
    avg_score = team_games["team_score"].mean()

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("Record", f"{wins}-{losses}", f"Win rate: {format_pct(team_games['is_win'].mean())}")
    with c2:
        metric_card("Net Rating", format_value(avg_net), "Average per 100 possessions")
    with c3:
        metric_card("Off Rating", format_value(avg_off), "How efficiently this team scores")
    with c4:
        metric_card("Def Rating", format_value(avg_def), "Lower is better")
    with c5:
        metric_card("PPG", format_value(avg_score), f"Average pace: {format_value(team_games['pace'].mean())}")

    trend_metric = st.selectbox(
        "Trend metric",
        ["team_score", "net_rating", "off_rating", "def_rating", "pace", "effective_fg_pct"],
        format_func=lambda value: value.replace("_", " ").title(),
    )
    rolling = team_games[["game_datetime", trend_metric, "result_label"]].copy()
    rolling["rolling_value"] = rolling[trend_metric].rolling(5, min_periods=1).mean()
    fig_trend = px.line(
        rolling,
        x="game_datetime",
        y="rolling_value",
        markers=True,
        title=f"{selected_team}: 5-Game Rolling {trend_metric.replace('_', ' ').title()}",
        color_discrete_sequence=[SECONDARY],
    )
    fig_trend = apply_chart_style(fig_trend)

    home_split = (
        team_games.groupby("home_away", as_index=False)
        .agg(win_pct=("is_win", "mean"), avg_score=("team_score", "mean"), avg_allowed=("opponent_score", "mean"))
        .sort_values("home_away")
    )
    fig_split = make_subplots(specs=[[{"secondary_y": True}]])
    fig_split.add_bar(
        x=home_split["home_away"],
        y=home_split["avg_score"],
        name="avg_score",
        marker_color=SECONDARY,
        secondary_y=False,
    )
    fig_split.add_bar(
        x=home_split["home_away"],
        y=home_split["avg_allowed"],
        name="avg_allowed",
        marker_color="#7A8B99",
        secondary_y=False,
    )
    fig_split.add_scatter(
        x=home_split["home_away"],
        y=home_split["win_pct"] * 100,
        name="win_pct",
        mode="lines+markers",
        line=dict(color=ACCENT, width=3),
        marker=dict(size=9),
        secondary_y=True,
    )
    fig_split.update_layout(
        title="Home vs Away Split",
        barmode="group",
    )
    fig_split.update_yaxes(title_text="Points", secondary_y=False)
    fig_split.update_yaxes(title_text="Win %", secondary_y=True)
    fig_split = apply_chart_style(fig_split)

    points_profile = (
        team_games[
            ["points_fast_break", "points_from_turnovers", "points_in_the_paint", "points_second_chance", "bench_points"]
        ]
        .mean()
        .reset_index()
    )
    points_profile.columns = ["category", "value"]
    fig_profile = px.bar(
        points_profile,
        x="value",
        y="category",
        orientation="h",
        color="value",
        color_continuous_scale="Blues",
        title="Average Scoring Sources",
        labels={"value": "Points per game", "category": ""},
    )
    fig_profile = apply_chart_style(fig_profile)

    col_a, col_b = st.columns([1.4, 1])
    with col_a:
        st.plotly_chart(fig_trend, width="stretch")
    with col_b:
        st.plotly_chart(fig_split, width="stretch")

    st.plotly_chart(fig_profile, width="stretch")

    recent_games = team_games.sort_values("game_datetime", ascending=False).head(12).copy()
    recent_games["game_date"] = recent_games["game_datetime"].dt.strftime("%Y-%m-%d")
    recent_games["result"] = recent_games["is_win"].map({1: "W", 0: "L"})
    recent_games["matchup"] = recent_games["opponent_team_city"] + " " + recent_games["opponent_team_name"]
    st.dataframe(
        recent_games[
            ["game_date", "game_type", "result", "home_away", "matchup", "team_score", "opponent_score", "net_rating", "pace"]
        ],
        width="stretch",
        hide_index=True,
    )


elif page == "Player Explorer":
    st.markdown(
        "Use this page to compare player roles, usage, and efficiency."
    )
    min_games = st.slider("Minimum games played", min_value=1, max_value=40, value=10)
    team_filter = st.selectbox("Team filter", ["All teams"] + dim_team["team_full_name"].sort_values().tolist())

    player_pool = filtered_player_games.copy()
    if team_filter != "All teams":
        selected_team_row = dim_team.loc[dim_team["team_full_name"] == team_filter].iloc[0]
        player_pool = player_pool.loc[player_pool["team_id"] == selected_team_row["team_id"]]

    player_summary = (
        player_pool.groupby("player_id", as_index=False)
        .agg(
            games=("game_id", "nunique"),
            points=("points", "mean"),
            assists=("assists", "mean"),
            rebounds=("total_rebounds", "mean"),
            minutes=("minutes_played", "mean"),
            true_shooting_pct=("true_shooting_pct", "mean"),
            usage_pct=("usage_pct", "mean"),
            net_rating=("net_rating", "mean"),
        )
        .query("games >= @min_games")
    )
    player_summary = player_summary.merge(dim_player[["player_id", "player_full_name"]], on="player_id", how="left")

    if player_summary.empty:
        st.info("No players match the current filters. Try lowering the minimum games or changing the team filter.")
        st.stop()

    leaderboard_metric = st.selectbox(
        "Leaderboard metric",
        ["points", "assists", "rebounds", "true_shooting_pct", "usage_pct", "net_rating"],
        format_func=lambda value: value.replace("_", " ").title(),
    )

    leaders = player_summary.sort_values(leaderboard_metric, ascending=False).head(15)
    fig_leaders = px.bar(
        leaders.sort_values(leaderboard_metric),
        x=leaderboard_metric,
        y="player_full_name",
        orientation="h",
        color="minutes",
        color_continuous_scale="Tealgrn",
        title=f"Top Players by {leaderboard_metric.replace('_', ' ').title()}",
        labels={"player_full_name": "", leaderboard_metric: leaderboard_metric.replace("_", " ").title()},
    )
    fig_leaders = apply_chart_style(fig_leaders)
    st.plotly_chart(fig_leaders, width="stretch")

    player_names = player_summary["player_full_name"].dropna().sort_values().tolist()
    selected_player_name = st.selectbox("Choose a player", player_names)
    selected_player_row = dim_player.loc[dim_player["player_full_name"] == selected_player_name].iloc[0]
    player_games = player_pool.loc[player_pool["player_id"] == selected_player_row["player_id"]].sort_values("game_datetime")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("PPG", format_value(player_games['points'].mean()), f"Games: {player_games['game_id'].nunique()}")
    with c2:
        metric_card("APG", format_value(player_games['assists'].mean()), "Assists per game")
    with c3:
        metric_card("RPG", format_value(player_games['total_rebounds'].mean()), "Rebounds per game")
    with c4:
        metric_card("TS%", format_pct(player_games['true_shooting_pct'].mean()), "Scoring efficiency")
    with c5:
        metric_card("Usage%", format_pct(player_games['usage_pct'].mean()), f"Avg net rating: {format_value(player_games['net_rating'].mean())}")

    trend_columns = st.multiselect(
        "Game-by-game trend",
        ["points", "assists", "total_rebounds", "minutes_played", "true_shooting_pct", "usage_pct"],
        default=["points", "assists", "total_rebounds"],
        format_func=lambda value: value.replace("_", " ").title(),
    )
    if trend_columns:
        fig_player_trend = px.line(
            player_games,
            x="game_datetime",
            y=trend_columns,
            markers=True,
            color_discrete_sequence=TEAM_COLORS,
            title=f"{selected_player_name}: Game Log Trends",
        )
        fig_player_trend = apply_chart_style(fig_player_trend)
        st.plotly_chart(fig_player_trend, width="stretch")

    recent_log = player_games.sort_values("game_datetime", ascending=False).head(12).copy()
    recent_log["game_date"] = recent_log["game_datetime"].dt.strftime("%Y-%m-%d")
    recent_log["matchup"] = recent_log["opponent_team_city"] + " " + recent_log["opponent_team_name"]
    st.dataframe(
        recent_log[
            [
                "game_date",
                "game_type",
                "matchup",
                "minutes_played",
                "points",
                "assists",
                "total_rebounds",
                "true_shooting_pct",
                "usage_pct",
                "net_rating",
            ]
        ],
        width="stretch",
        hide_index=True,
    )
