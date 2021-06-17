from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Iterator

from dcp.data_format import Records
from dcp.utils.common import ensure_datetime, utcnow
from requests.auth import HTTPBasicAuth
from snapflow import datafunction, Context, DataBlock
from snapflow.core.extraction.connection import JsonHttpApiConnection
from snapflow_stripe.functions.import_charges import stripe_importer

if TYPE_CHECKING:
    from snapflow_stripe import StripeSubscriptionRaw


STRIPE_API_BASE_URL = "https://api.stripe.com/v1/"
MIN_DATE = datetime(2006, 1, 1)


@datafunction(
    namespace="stripe", display_name="Import Stripe subscriptions",
)
def import_subscriptions(
    ctx: Context, api_key: str, curing_window_days: int = 90
) -> Iterator[Records[StripeSubscriptionRaw]]:
    yield from stripe_importer(
        "subscriptions",
        ctx,
        api_key,
        curing_window_days=curing_window_days,
        extra_params={"status": "all"},
    )
