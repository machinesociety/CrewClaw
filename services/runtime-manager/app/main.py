from fastapi import FastAPI

app = FastAPI(
    title="Runtime Manager",
    version="0.1.0",
    description="Internal Runtime Manager service bootstrap endpoint.",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "runtime-manager", "status": "ok"}


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "healthy"}
