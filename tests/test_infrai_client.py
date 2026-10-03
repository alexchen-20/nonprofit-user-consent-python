import httpx
import pytest

from nonprofit_consent.infrai_client import InfraiClient, InfraiError


@pytest.mark.asyncio
async def test_captcha_business_rejection_preserves_envelope_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/captcha/verify"
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            422,
            json={
                "ok": False,
                "data": None,
                "error": {"code": "CAPTCHA_SCORE_TOO_LOW", "message": "Try again"},
                "metadata": {},
            },
        )

    client = InfraiClient(api_key="test-key", transport=httpx.MockTransport(handler))
    with pytest.raises(InfraiError) as caught:
        await client.verify_captcha("captcha-token", "grant_consent")
    await client.close()

    assert caught.value.status_code == 422
    assert caught.value.code == "CAPTCHA_SCORE_TOO_LOW"

