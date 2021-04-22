from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
from snapflow import datafunction, Context, DataBlock

if TYPE_CHECKING:
    from snapflow_stripe import StripeCharge, StripeChargeRaw


@datafunction("clean_charges", namespace="stripe", display_name="Clean Stripe charges")
def clean_charges(charges: DataBlock[StripeChargeRaw]) -> DataBlock[StripeCharge]:
    df = charges.as_dataframe()
    df["created"] = pd.to_datetime(df["created"], unit="s")
    return df
