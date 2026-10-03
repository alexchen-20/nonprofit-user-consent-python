from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from threading import Lock

from pydantic import BaseModel, ConfigDict, Field


class ConsentScope(StrEnum):
    DONOR_RECEIPTS = "donor_receipts"
    VOLUNTEER_REMINDERS = "volunteer_reminders"
    CAMPAIGN_REPORTING = "campaign_reporting"


class GrantConsentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=8, max_length=100)
    user_id: str = Field(min_length=1, max_length=100)
    scopes: set[ConsentScope] = Field(min_length=1)
    captcha_token: str = Field(min_length=1)
    widget_record_id: str = Field(default="default", min_length=1)


class RevokeConsentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=8, max_length=100)
    user_id: str = Field(min_length=1, max_length=100)
    scopes: set[ConsentScope] = Field(min_length=1)


class ConsentState(BaseModel):
    user_id: str
    granted_scopes: set[ConsentScope]
    updated_at: datetime


class ConsentLedger:
    """Small in-memory ledger for the runnable example."""

    def __init__(self) -> None:
        self._scopes: dict[str, set[ConsentScope]] = {}
        self._results: dict[str, ConsentState] = {}
        self._lock = Lock()

    def grant(self, request: GrantConsentRequest) -> ConsentState:
        return self._apply(request.request_id, request.user_id, request.scopes, grant=True)

    def revoke(self, request: RevokeConsentRequest) -> ConsentState:
        return self._apply(request.request_id, request.user_id, request.scopes, grant=False)

    def get(self, user_id: str) -> ConsentState:
        with self._lock:
            return self._snapshot(user_id)

    def permits(self, user_id: str, scope: ConsentScope) -> bool:
        with self._lock:
            return scope in self._scopes.get(user_id, set())

    def _apply(
        self,
        request_id: str,
        user_id: str,
        scopes: set[ConsentScope],
        grant: bool,
    ) -> ConsentState:
        with self._lock:
            previous = self._results.get(request_id)
            if previous is not None:
                return previous.model_copy(deep=True)
            current = self._scopes.setdefault(user_id, set())
            current.update(scopes) if grant else current.difference_update(scopes)
            result = self._snapshot(user_id)
            self._results[request_id] = result
            return result.model_copy(deep=True)

    def _snapshot(self, user_id: str) -> ConsentState:
        return ConsentState(
            user_id=user_id,
            granted_scopes=set(self._scopes.get(user_id, set())),
            updated_at=datetime.now(timezone.utc),
        )
