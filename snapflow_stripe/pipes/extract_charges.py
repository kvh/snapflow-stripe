from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from requests.auth import HTTPBasicAuth
from snapflow import PipeContext, pipe
from snapflow.core.data_formats import RecordsList, RecordsListGenerator
from snapflow.core.extraction.connection import JsonHttpApiConnection
from snapflow.utils.common import ensure_datetime, utcnow

STRIPE_API_BASE_URL = "https://api.stripe.com/v1/"
MIN_DATE = datetime(2006, 1, 1)


@dataclass
class ExtractStripeConfig:
    api_key: str
    curing_window_days: int = 90


@dataclass
class ExtractStripeChargesState:
    latest_extracted_at: datetime


@pipe(
    "extract_charges",
    module="stripe",
    config_class=ExtractStripeConfig,
    state_class=ExtractStripeChargesState,
)
def extract_charges(ctx: PipeContext) -> RecordsListGenerator[StripeChargeRaw]:
    """
    Stripe doesn't have a way to request by "updated at" times, so we must
    refresh old records according to our own logic. We use a "curing window"
    to re-extract records up to one year (the default) old.
    """
    api_key = ctx.get_config_value("api_key")
    curing_window_days = ctx.get_config_value("curing_window_days", 90)
    latest_extracted_at = ctx.get_state_value("latest_extracted_at")
    latest_extracted_at = ensure_datetime(latest_extracted_at)
    params = {
        "limit": 100,
    }
    if latest_extracted_at:
        # Extract only more recent than latest extracted at date, offset by a curing window
        # (default 90 days) to capture updates to objects (refunds, etc)
        params["created[gt]"] = int(
            (latest_extracted_at - timedelta(days=curing_window_days)).timestamp()
        )
    conn = JsonHttpApiConnection()
    endpoint_url = STRIPE_API_BASE_URL + "charges"
    while ctx.should_continue():
        resp = conn.get(endpoint_url, params, auth=HTTPBasicAuth(api_key, ""))
        json_resp = resp.json()
        assert isinstance(json_resp, dict)
        records = json_resp["data"]
        if len(records) == 0:
            # All done
            break
        yield records
        latest_object_id = records[-1]["id"]
        if not json_resp.get("has_more"):
            break
        params["starting_after"] = latest_object_id
    # We only update state if we have fetched EVERYTHING available as of now
    ctx.emit_state_value("latest_extracted_at", utcnow())
