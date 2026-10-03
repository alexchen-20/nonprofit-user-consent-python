from nonprofit_consent.consent_service import (
    ConsentLedger,
    ConsentScope,
    GrantConsentRequest,
    RevokeConsentRequest,
)


def test_revocation_stops_one_workflow_and_keeps_the_other() -> None:
    ledger = ConsentLedger()
    ledger.grant(
        GrantConsentRequest(
            request_id="grant-user-17",
            user_id="user-17",
            scopes={
                ConsentScope.DONOR_RECEIPTS,
                ConsentScope.VOLUNTEER_REMINDERS,
            },
            captcha_token="test-captcha-token",
        )
    )

    state = ledger.revoke(
        RevokeConsentRequest(
            request_id="revoke-user-17-reminders",
            user_id="user-17",
            scopes={ConsentScope.VOLUNTEER_REMINDERS},
        )
    )

    assert state.granted_scopes == {ConsentScope.DONOR_RECEIPTS}
    assert ledger.permits("user-17", ConsentScope.DONOR_RECEIPTS)
    assert not ledger.permits("user-17", ConsentScope.VOLUNTEER_REMINDERS)


def test_replaying_a_grant_request_does_not_change_its_result() -> None:
    ledger = ConsentLedger()
    request = GrantConsentRequest(
        request_id="grant-user-22",
        user_id="user-22",
        scopes={ConsentScope.CAMPAIGN_REPORTING},
        captcha_token="test-captcha-token",
    )

    first = ledger.grant(request)
    ledger.revoke(
        RevokeConsentRequest(
            request_id="revoke-user-22-reporting",
            user_id="user-22",
            scopes={ConsentScope.CAMPAIGN_REPORTING},
        )
    )
    replay = ledger.grant(request)

    assert replay == first
    assert not ledger.permits("user-22", ConsentScope.CAMPAIGN_REPORTING)

