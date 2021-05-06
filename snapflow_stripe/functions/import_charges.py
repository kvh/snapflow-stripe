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
    from snapflow_stripe import StripeChargeRaw


STRIPE_API_BASE_URL = "https://api.stripe.com/v1/"
MIN_DATE = datetime(2006, 1, 1)


@dataclass
class ImportStripeChargesState:
    latest_imported_at: datetime


@datafunction(
    "import_charges",
    namespace="stripe",
    state_class=ImportStripeChargesState,
    display_name="Import Stripe charges",
)
def import_charges(
    ctx: Context, api_key: str, curing_window_days: int = 90
) -> Iterator[Records[StripeChargeRaw]]:
    """
    Stripe doesn't have a way to request by "updated at" times, so we must
    refresh old records according to our own logic. We use a "curing window"
    to re-import records up to one year (the default) old.
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
            (latest_imported_at - timedelta(days=int(curing_window_days))).timestamp()
        )
    conn = JsonHttpApiConnection()
    endpoint_url = STRIPE_API_BASE_URL + "charges"
    all_done = False
    while ctx.should_continue():
        resp = conn.get(endpoint_url, params, auth=HTTPBasicAuth(api_key, ""))
        json_resp = resp.json()
        assert isinstance(json_resp, dict)
        records = json_resp["data"]
        if len(records) == 0:
            # All done
            all_done = True
            break
        yield records
        latest_object_id = records[-1]["id"]
        if not json_resp.get("has_more"):
            all_done = True
            break
        params["starting_after"] = latest_object_id
    # We only update state if we have fetched EVERYTHING available as of now
    if all_done:
        ctx.emit_state_value("latest_imported_at", utcnow())
