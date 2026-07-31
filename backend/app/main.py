from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def get_health() -> dict:
    return {"status": "ok"}
