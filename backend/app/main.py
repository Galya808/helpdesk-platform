from fastapi import FastAPI

app = FastAPI(title="Helpdesk API")


@app.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}
