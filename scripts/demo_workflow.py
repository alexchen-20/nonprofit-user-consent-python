import json
import os
import urllib.request


def post(path: str, body: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        f"{os.environ.get('CONSENT_SERVICE_URL', 'http://127.0.0.1:8000')}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def main() -> None:
    user_id = "donor_1042"
    granted = post(
        "/consents/grant",
        {
            "request_id": "demo-grant-1042",
            "user_id": user_id,
            "scopes": ["donor_receipts", "campaign_reporting"],
            "captcha_token": os.environ["CAPTCHA_TOKEN"],
            "widget_record_id": os.environ["WIDGET_RECORD_ID"],
        },
    )
    revoked = post(
        "/consents/revoke",
        {
            "request_id": "demo-revoke-1042",
            "user_id": user_id,
            "scopes": ["campaign_reporting"],
        },
    )
    print(json.dumps({"after_grant": granted, "after_revoke": revoked}, indent=2))


if __name__ == "__main__":
    main()
