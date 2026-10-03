from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Request

from .consent_service import (
    ConsentLedger,
    ConsentState,
    GrantConsentRequest,
    RevokeConsentRequest,
)
from .infrai_client import InfraiClient, InfraiError


ledger = ConsentLedger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client = InfraiClient()
    app.state.infrai = client
    yield
    await client.close()


service = FastAPI(title="Nonprofit consent service", lifespan=lifespan)


def get_infrai(request: Request) -> InfraiClient:
    return request.app.state.infrai


@service.post("/consents/grant", response_model=ConsentState)
async def grant_consent(
    body: GrantConsentRequest,
    infrai: InfraiClient = Depends(get_infrai),
) -> ConsentState:
    try:
        await infrai.verify_captcha(
            body.captcha_token,
            action="grant_consent",
            widget_record_id=body.widget_record_id,
        )
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    return ledger.grant(body)


@service.post("/consents/revoke", response_model=ConsentState)
async def revoke_consent(body: RevokeConsentRequest) -> ConsentState:
    return ledger.revoke(body)


@service.get("/consents/{user_id}", response_model=ConsentState)
async def read_consent(user_id: str) -> ConsentState:
    return ledger.get(user_id)
