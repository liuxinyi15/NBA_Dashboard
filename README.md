# NBA 2025-26 Performance Dashboard

This project builds a deployable dashboard from the NBA datasets in `archive/` and explicitly models the data as a star schema.

The repository ships with prebuilt star-schema tables in `data/star_schema/` so the app can run and deploy without the original raw extracts.

## What is included

- A star schema with:
  - `fact_team_game`: one row per team per game
  - `fact_player_game`: one row per player per game
  - `dim_date`
  - `dim_team`
  - `dim_game`
  - `dim_player`
- A Streamlit dashboard with four views:
  - Overview
  - Team Explorer
  - Player Explorer
  - Star Schema
- Deployment-ready files:
  - `requirements.txt`
  - `.streamlit/config.toml`
  - `Dockerfile`

## Project structure

- `app.py`: Streamlit application
- `src/build_star_schema.py`: ETL that builds the dimensions and fact tables from raw CSV files
- `src/dashboard_data.py`: cached loading helpers for the dashboard
- `data/star_schema/`: generated star-schema tables

## How the star schema works

- `fact_team_game`
  - Grain: one row per team per game
  - Stores scores, shooting, rebounding, pace, ratings, and four-factor metrics
- `fact_player_game`
  - Grain: one row per player per game
  - Stores box score stats plus advanced efficiency and usage metrics
- `dim_team`
  - Team metadata from `TeamHistories.csv`
- `dim_player`
  - Player metadata from `Players.csv`
- `dim_game`
  - Game context such as arena, attendance, and matchup structure
- `dim_date`
  - Calendar attributes used for filtering and time-series analysis

## Run locally

```bash
python src/build_star_schema.py
streamlit run app.py
```

## Run URL

```bash
https://nbadashboard-72k4wn4rmh9fija9dam2ot.streamlit.app/
```
