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
    ctx: Context, api_key: str, curing_window_days: int = 90
) -> Iterator[Records[StripeSubscriptionItemRaw]]:
    """
    # TODO: repeated code
    """
    latest_full_import_at = ctx.get_state_value("latest_full_import_at")
    latest_full_import_at = ensure_datetime(latest_full_import_at)
    current_starting_after = ctx.get_state_value("current_starting_after")
    params = {
        "limit": 100,
        "status": "all",
    }
    # if earliest_created_at_imported <= latest_full_import_at - timedelta(days=int(curing_window_days)):
    if latest_full_import_at and curing_window_days:
        # Import only more recent than latest imported at date, offset by a curing window
        # (default 90 days) to capture updates to objects (refunds, etc)
        params["created[gte]"] = int(
            (
                latest_full_import_at - timedelta(days=int(curing_window_days))
            ).timestamp()
        )
    if current_starting_after:
        params["starting_after"] = current_starting_after
    conn = JsonHttpApiConnection()
    endpoint_url = STRIPE_API_BASE_URL + "subscriptions"
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

        latest_object_id = records[-1]["id"]
        if not json_resp.get("has_more"):
            all_done = True
            break
        params["starting_after"] = latest_object_id
        ctx.emit_state_value("current_starting_after", latest_object_id)
    else:
        # Don't update any state, we just timed out
        return
    # We only update state if we have fetched EVERYTHING available as of now
    if all_done:
        ctx.emit_state_value("latest_imported_at", utcnow())
        # IMPORTANT: we reset the starting after cursor so we start from the beginning again on next run
        ctx.emit_state_value("current_starting_after", None)

