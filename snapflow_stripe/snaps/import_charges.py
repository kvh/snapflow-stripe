from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from requests.auth import HTTPBasicAuth
from snapflow import SnapContext, Snap, Param
from snapflow.storage.data_formats import Records, RecordsIterator
from snapflow.core.extraction.connection import JsonHttpApiConnection
from snapflow.utils.common import ensure_datetime, utcnow

if TYPE_CHECKING:
    from snapflow_stripe import StripeChargeRaw


STRIPE_API_BASE_URL = "https://api.stripe.com/v1/"
MIN_DATE = datetime(2006, 1, 1)



@dataclass
class ImportStripeChargesState:
    latest_imported_at: datetime


@Snap(
    "import_charges",
    module="stripe",
    state_class=ImportStripeChargesState,
    display_name="Import Stripe charges",
)
@Param("api_key", "str")
@Param("curing_window_days", "int", default=90)
def import_charges(ctx: SnapContext) -> RecordsIterator[StripeChargeRaw]:
    """
    Stripe doesn't have a way to request by "updated at" times, so we must
    refresh old records according to our own logic. We use a "curing window"
    to re-import records up to one year (the default) old.
    """
    api_key = ctx.get_param("api_key")
    curing_window_days = ctx.get_param("curing_window_days", 90)
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
    ctx.emit_state_value("latest_imported_at", utcnow())
