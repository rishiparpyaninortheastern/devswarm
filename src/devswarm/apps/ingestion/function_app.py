import json

import azure.functions as func
from pydantic import ValidationError

from devswarm.agents.atlas import accept
from devswarm.shared.contracts import Incident
from devswarm.shared.observability import record
from devswarm.shared.runtime import store

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="incidents", methods=["POST"])
def incidents(req: func.HttpRequest) -> func.HttpResponse:
    try:
        incident = Incident.model_validate(req.get_json())
    except (ValueError, ValidationError):
        record("incident.rejected")
        return func.HttpResponse(
            '{"detail":"Invalid incident schema"}', status_code=422, mimetype="application/json"
        )
    receipt = accept(store(), incident)
    return func.HttpResponse(
        json.dumps(receipt.model_dump()), status_code=202, mimetype="application/json"
    )
