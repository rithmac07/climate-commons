from fastapi import FastAPI

app = FastAPI(
	title="Climate Commons API",
	version="0.1.0",
	description="Screen-reader-first climate data reporting API.",
)


@app.get("/health")
def health_check() -> dict[str, str]:
	return {"status": "ok"}
