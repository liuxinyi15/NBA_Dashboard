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

The app can also build the star schema automatically the first time it starts if `data/star_schema/` does not exist and the raw source files are present in `archive/`.

## Deployment

### Option 1: Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. Create a new app on Streamlit Community Cloud.
3. Set the main file path to `app.py`.
4. Deploy.

Because the app generates `data/star_schema/` automatically on first launch, no extra build command is required.

### Option 2: Render or Railway

This repository includes a `Dockerfile`, so you can deploy it directly as a Docker web service.

Recommended container command:

```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT
```

## Suggested submission note

You can describe the project like this in your assignment:

> I built a deployable NBA analytics dashboard for the 2025-26 season. The dashboard is backed by a star schema with two fact tables (`fact_team_game`, `fact_player_game`) and four dimensions (`dim_date`, `dim_team`, `dim_game`, `dim_player`). It is implemented in Streamlit and can be shared through a public URL after deployment.
