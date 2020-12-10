from __future__ import annotations

import pandas as pd
from snapflow import DataBlock, pipe, sql_pipe


@pipe(
    "clean_charges",
    module="stripe",
)
def clean_charges(
    charges: DataBlock[stripe.StripeChargeRaw],
) -> DataBlock[stripe.StripeCharge]:
    df = charges.as_dataframe()
    df["created"] = pd.to_datetime(df["created"], unit="s")
    return df
