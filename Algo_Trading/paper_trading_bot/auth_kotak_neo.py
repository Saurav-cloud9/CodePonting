"""
auth_kotak_neo.py — shared Kotak Neo session + quote/candle fetch helpers.
Used by every strategy script in strategies/ for PAPER trading (data access only —
never places real orders; see place_paper_order() below).

STATUS: STUB. Kotak Neo developer API access is not set up yet (as of 2026-07-11).
Strategy scripts import this at the top, but nothing in it is called until a bot
is actually run — so this file being incomplete does not block writing the
strategy scripts themselves.

Once Kotak Neo developer access exists:
  1. pip install neo-api-client
  2. Set KOTAK_NEO_CONSUMER_KEY / KOTAK_NEO_CONSUMER_SECRET / KOTAK_NEO_MOBILE /
     KOTAK_NEO_MPIN as environment variables (never hardcode credentials in this file).
  3. Verify method names below against the actual neo-api-client version installed —
     Kotak's SDK login flow has changed across versions.
"""

import os

CONSUMER_KEY = os.environ.get("KOTAK_NEO_CONSUMER_KEY", "")
CONSUMER_SECRET = os.environ.get("KOTAK_NEO_CONSUMER_SECRET", "")
MOBILE_NUMBER = os.environ.get("KOTAK_NEO_MOBILE", "")
MPIN = os.environ.get("KOTAK_NEO_MPIN", "")

_client = None


def get_session():
    """Returns an authenticated NeoAPI client, logging in on first call."""
    global _client
    if _client is not None:
        return _client

    if not all([CONSUMER_KEY, CONSUMER_SECRET, MOBILE_NUMBER, MPIN]):
        raise RuntimeError(
            "Kotak Neo credentials not configured. Set KOTAK_NEO_CONSUMER_KEY, "
            "KOTAK_NEO_CONSUMER_SECRET, KOTAK_NEO_MOBILE, KOTAK_NEO_MPIN as "
            "environment variables before running any bot script."
        )

    from neo_api_client import NeoAPI  # deferred import — only needed once credentials exist

    client = NeoAPI(
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        environment="prod",
    )
    client.login(mobilenumber=MOBILE_NUMBER, password=MPIN)
    client.session_2fa()  # TOTP/OTP step — exact call TBD against installed SDK version

    _client = client
    return _client


def get_latest_candle(symbol: str, interval: str = "5minute"):
    """
    Fetch the most recently completed candle for `symbol`.
    Placeholder — wire up against the installed neo-api-client's actual
    quote/historical-data method once credentials are live.
    """
    get_session()
    raise NotImplementedError(
        "get_latest_candle() not wired up yet — needs live Kotak Neo access "
        "to confirm the SDK's actual candle-fetch method and response shape."
    )


def get_warmup_candles(symbol: str, count: int = 30, interval: str = "5minute"):
    """
    Fetch the last `count` completed candles for `symbol` before market open,
    so MA20/ATR14 have enough history to be valid from the first live bar.
    Placeholder — wire up against neo-api-client's historical-data method once
    credentials are live.
    """
    get_session()
    raise NotImplementedError(
        "get_warmup_candles() not wired up yet — needs live Kotak Neo access "
        "to confirm the SDK's historical-data method and response shape."
    )


def place_paper_order(*args, **kwargs):
    """
    Paper trading NEVER calls the broker's real order placement endpoint.
    This function intentionally does nothing except raise, so there is one
    obvious place that would fail loudly if a bot script accidentally tried
    to route a paper trade through the live order path.
    """
    raise RuntimeError(
        "place_paper_order() should never be called. Paper trades are simulated "
        "locally against live quotes/candles, not sent to the broker."
    )
