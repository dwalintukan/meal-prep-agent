from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


# MUST BE LAST ROUTE!
# Serves the React static page.
@app.get("/{full_path:path}")
async def spa_fallback():
    return FileResponse("frontend/dist/index.html")
