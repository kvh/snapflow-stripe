from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Iterator

from dcp.data_format import Records
from dcp.utils.common import ensure_datetime, utcnow
from requests.auth import HTTPBasicAuth
from snapflow import datafunction, Context, DataBlock
from snapflow.core.extraction.connection import JsonHttpApiConnection

if TYPE_CHECKING:
    from snapflow_stripe import StripeRefundRaw


STRIPE_API_BASE_URL = "https://api.stripe.com/v1/"
MIN_DATE = datetime(2006, 1, 1)


# TODO: DRY!


@datafunction(
    "import_refunds", namespace="stripe", display_name="Import Stripe refunds",
)
def import_refunds(
    ctx: Context, api_key: str, curing_window_days: int = 90
) -> Iterator[Records[StripeRefundRaw]]:
    """
    Stripe doesn't have a way to request by "updated at" times, so we must
    refresh old records according to our own logic. We use a "curing window"
    to re-import records up to 90 dyas (the default) old.
    """
    latest_imported_at = ctx.get_state_value("latest_imported_at")
    latest_imported_at = ensure_datetime(latest_imported_at)
    params = {
        "limit": 100,
    }
    if latest_imported_at:
        # Import only more recent than latest imported at date, offset by a curing window
        # (default 90 days) to capture updates to objects (refunds, etc)
        params["created[gt]"] = int(
            (latest_imported_at - timedelta(days=curing_window_days)).timestamp()
        )
    conn = JsonHttpApiConnection()
    endpoint_url = STRIPE_API_BASE_URL + "refunds"
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
    ctx.emit_state_value("latest_imported_at", utcnow())
