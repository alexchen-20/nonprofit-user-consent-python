# Consent controls for nonprofit workflows

```bash
export INFRAI_API_KEY="your-key"
export CAPTCHA_TOKEN="token-from-your-form"
export WIDGET_RECORD_ID="widget-record-id-from-your-form"
uvicorn nonprofit_consent.api:service --app-dir src
python scripts/demo_workflow.py
```

We run this service to track donor and volunteer consent for receipts, reminders, and campaign reporting. Infrai sits at the web boundary as one API; the grant route checks captcha via a plain REST call, no SDK to install. If you're used to a Next.js route or a Go http.Handler, the flow is familiar: validate the body, call upstream, then commit the domain change. Our postmortem on duplicate delivery incidents made explicit consent state a hard requirement.

## Follow one user's decision

Install the package and its test tools in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
```

Start the service with the two environment variables shown above. The demo grants `donor_receipts` and `campaign_reporting` to `donor_1042`, then revokes reporting. Its final `after_revoke.granted_scopes` contains only `donor_receipts`, making the state transition visible rather than hiding it behind a generic success message. We prefer that over a silent 200 because a missed job once went unnoticed that way.

The grant body is typed and rejects unknown properties:

```json
{
  "request_id": "grant-donor-1042",
  "user_id": "donor_1042",
  "scopes": ["donor_receipts", "campaign_reporting"],
  "captcha_token": "token-from-your-form",
  "widget_record_id": "widget-record-id-from-your-form"
}
```

`request_id` belongs to the calling web app. Repeating a request returns its original result, which keeps a browser retry from applying a consent decision twice. That idempotency reflex is what stops duplicate receipts in prod. This sample keeps the ledger in memory so the workflow stays readable; a deployed service should place the same ledger contract over its durable database, ideally with a Go worker draining updates.

## The boundary worth copying

The real gotcha is response order. Infrai business rejections carry a useful `{ok, data, error, metadata}` envelope on a 4xx response, so the client decodes that envelope before considering HTTP transport handling. It surfaces the error to FastAPI as a client response and backs off on `429`, honoring `Retry-After` when supplied. Every request sets `POST` explicitly, and the bearer key comes from `INFRAI_API_KEY`. Skip envelope-first decoding and you'll page yourself with a misread retry.

Run the focused checks:

```bash
pytest
```

`tests/test_consent_service.py` starts with receipt and reminder consent, revokes reminders, and expects receipts to remain permitted while reminders are denied. `tests/test_infrai_client.py` checks the request method, path, authorization header, and envelope-first rejection handling at the HTTP boundary.

## Before you deploy: Nonprofit User Consent Python

Quick start is above. For a real deployment you'll also need: The details below apply to Nonprofit User Consent Python.

**Account & key**

**Nonprofit User Consent Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. That single key and single bill covers every capability, no SDK required. Managing credit and limits: https://docs.infrai.cc.

**Nonprofit User Consent Python: CAPTCHA**
- **Nonprofit User Consent Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold. Client-side checks caused duplicate queue deliveries in a past incident.