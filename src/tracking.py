import asyncio
import logging
import os

import httpx

logger = logging.getLogger(__name__)

MATOMO_URL = os.getenv("MATOMO_URL")
MATOMO_SITE_ID = os.getenv("MATOMO_SITE_ID", "1")
MATOMO_TOKEN_AUTH = os.getenv("MATOMO_TOKEN_AUTH")
_client: httpx.AsyncClient | None = None


async def init_client():
    global _client
    if MATOMO_URL:
        _client = httpx.AsyncClient(base_url=MATOMO_URL, timeout=5.0)
        logger.info("Matomo tracking enabled: %s (site %s)", MATOMO_URL, MATOMO_SITE_ID)
    else:
        logger.info("Matomo tracking disabled (MATOMO_URL not set)")


async def close_client():
    if _client:
        await _client.aclose()


def track_page_view(request) -> None:
    if not _client:
        return
    params = {
        "idsite": MATOMO_SITE_ID,
        "rec": 1,
        "url": str(request.url),
        "action_name": request.url.path,
        "ua": request.headers.get("user-agent", ""),
        "lang": request.headers.get("accept-language", ""),
        "apiv": 1,
        "send_image": 0,
    }
    if MATOMO_TOKEN_AUTH:
        params["token_auth"] = MATOMO_TOKEN_AUTH
        params["cip"] = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    referer = request.headers.get("referer")
    if referer:
        params["urlref"] = referer
    asyncio.create_task(_send(params))


async def _send(params: dict) -> None:
    try:
        resp = await _client.get("/matomo.php", params=params)
        logger.debug("Matomo response: %s", resp.status_code)
    except Exception:
        logger.warning("Matomo tracking request failed", exc_info=True)
