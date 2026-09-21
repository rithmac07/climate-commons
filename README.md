# Climate Commons

A screen-reader-friendly web application that reports annual global temperature anomalies from NASA GISTEMP v4 data.

## Features
- Reports the latest annual global temperature anomaly
- Calculates a five-year average anomaly
- Calculates a linear temperature trend in degrees Celsius per decade
- Lets users choose a start year and end year
- Rejects reversed ranges and ranges with fewer than five observations
- Includes an accessible annual-anomaly trend chart
- Provides status and error messages for screen-reader users

## Data source
This project uses NASA GISS Surface Temperature Analysis (GISTEMP v4) annual global temperature anomaly data.

Temperature anomalies describe how much warmer or cooler a period was relative to NASA's 1951–1980 baseline.

## Run locally

```zsh
git clone [https://github.com/rithmac07/climate-commons.git](https://github.com/rithmac07/climate-commons.git)
cd climate-commons

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
