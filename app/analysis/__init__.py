import pandas as pd

REQUIRED_COLUMNS = {"year", "anomaly_c"}


def validate_annual_series(df: pd.DataFrame) -> pd.DataFrame:
	missing_columns = REQUIRED_COLUMNS - set(df.columns)

	if missing_columns:
		raise ValueError(
			f"Missing required columns: {sorted(missing_columns)}"
		)

	clean = df.copy()

	clean["year"] = pd.to_numeric(clean["year"], errors="raise")
	clean["anomaly_c"] = pd.to_numeric(clean["anomaly_c"], errors="coerce")

	if clean["year"].isna().any():
		raise ValueError("Year values cannot be missing.")

	if (clean["year"] % 1 != 0).any():
		raise ValueError("Year values must be whole numbers.")

	clean["year"] = clean["year"].astype(int)

	if clean["year"].duplicated().any():
		duplicate_years = clean.loc[
			clean["year"].duplicated(), "year"
		].tolist()

		raise ValueError(f"Duplicate years found: {duplicate_years}")

	clean = clean.sort_values("year").reset_index(drop=True)

	if len(clean) < 3:
		raise ValueError(
			"At least three annual observations are required."
		)

	return clean
