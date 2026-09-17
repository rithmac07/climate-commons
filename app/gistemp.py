from io import StringIO
from pathlib import Path

import pandas as pd


GISTEMP_PATH = Path("data_fixtures/GLB.Ts+dSST.txt")


def load_gistemp_annual_data() -> pd.DataFrame:
    text = GISTEMP_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    header_index = next(
        index
        for index, line in enumerate(lines)
        if line.strip().startswith("Year")
    )

    table = pd.read_csv(
        StringIO("\n".join(lines[header_index:])),
        sep=r"\s+",
        na_values=["***", "*****"],
    )

    if "Year" not in table.columns or "J-D" not in table.columns:
        raise ValueError(
            "NASA data is missing the expected Year or J-D column."
        )

    data = table[["Year", "J-D"]].copy()
    data.columns = ["year", "anomaly_c"]

    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    data["anomaly_c"] = pd.to_numeric(
        data["anomaly_c"],
        errors="coerce",
    )

    data = data.dropna().copy()
    data["year"] = data["year"].astype(int)
    data["anomaly_c"] = data["anomaly_c"] / 100

    if data.empty:
        raise ValueError("No annual GISTEMP observations were found.")

    return data.sort_values("year").reset_index(drop=True)
