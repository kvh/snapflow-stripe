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
    from snapflow_stripe import StripeInvoiceRaw


STRIPE_API_BASE_URL = "https://api.stripe.com/v1/"
MIN_DATE = datetime(2006, 1, 1)


@datafunction(
    namespace="stripe", display_name="Import Stripe invoices",
)
def import_invoices(ctx: Context, api_key: str,) -> Iterator[Records[StripeInvoiceRaw]]:
    """
    Stripe doesn't have a way to request by "updated at" times, so we must
    refresh all records everytime.
    """
    params = {
        "limit": 100,
    }
    conn = JsonHttpApiConnection()
    endpoint_url = STRIPE_API_BASE_URL + "invoices"
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
