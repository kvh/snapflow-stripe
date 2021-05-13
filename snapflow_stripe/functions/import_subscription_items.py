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
    from snapflow_stripe import StripeSubscriptionItemRaw


STRIPE_API_BASE_URL = "https://api.stripe.com/v1/"


@datafunction(
    namespace="stripe", display_name="Import Stripe subscription items",
)
def import_subscription_items(
    ctx: Context, api_key: str,
) -> Iterator[Records[StripeSubscriptionItemRaw]]:
    """
    Stripe doesn't have a way to request by "updated at" times, so we must
    refresh all records everytime.
    """
    params = {
        "limit": 100,
        "status": "all",
    }
    conn = JsonHttpApiConnection()
    endpoint_url = STRIPE_API_BASE_URL + "subscriptions"
    while ctx.should_continue():
        resp = conn.get(endpoint_url, params, auth=HTTPBasicAuth(api_key, ""))
        json_resp = resp.json()
        assert isinstance(json_resp, dict)
        records = json_resp["data"]
        if len(records) == 0:
            # All done
            break
        for record in records:
            item_params = {
                "limit": 100,
                "subscription": record["id"],
            }
            while True:
                items_url = STRIPE_API_BASE_URL + "subscription_items"
                items_resp = conn.get(
                    items_url, item_params, auth=HTTPBasicAuth(api_key, "")
                )
                items_json_resp = items_resp.json()
                assert isinstance(items_json_resp, dict)
                items = items_json_resp["data"]
                if len(items) == 0:
                    # All done
                    break
                yield items
                if not items_json_resp.get("has_more"):
                    break
                latest_item_id = items[-1]["id"]
                item_params["starting_after"] = latest_item_id
            if not ctx.should_continue():
                break
        if not json_resp.get("has_more"):
            break
        latest_object_id = records[-1]["id"]
        params["starting_after"] = latest_object_id
