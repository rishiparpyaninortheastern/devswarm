from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from devswarm.agents.atlas import accept
from devswarm.shared.contracts import Incident, Receipt
from devswarm.shared.runtime import store

app = FastAPI(title="DevSwarm", version="0.1.0")


@app.exception_handler(RequestValidationError)
async def invalid_payload(request: Request, exc: RequestValidationError):
    # Do not echo possibly sensitive input in validation responses.
    return JSONResponse(status_code=422, content={"detail": "Invalid incident schema"})


@app.get("/health")
def health():
    return {"status": "ok", "mode": "local"}


@app.post("/incidents", response_model=Receipt, status_code=202)
def ingest(incident: Incident):
    return accept(store(), incident)


@app.get("/incidents/{fingerprint}")
def get_incident(fingerprint: str):
    result = store().get(fingerprint)
    if result is None:
        raise HTTPException(404, "Incident not found")
    return result
