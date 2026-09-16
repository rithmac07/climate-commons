import numpy as np
import pandas as pd


def add_five_year_average(df: pd.DataFrame) -> pd.DataFrame:
	result = df.copy()

	result["five_year_average_c"] = (
		result["anomaly_c"]
		.rolling(window=5, min_periods=5)
		.mean()
	)

	return result


def linear_trend_c_per_decade(df: pd.DataFrame) -> float:
	complete = df.dropna(subset=["year", "anomaly_c"])

	if len(complete) < 3:
		raise ValueError(
			"At least three complete observations are required for a trend."
		)

	slope_c_per_year, _ = np.polynomial.polynomial.polyfit(
		complete["year"],
		complete["anomaly_c"],
		deg=1,
	)

	return float(slope_c_per_year * 10)
