from typing import TypeVar

from snapflow import SnapflowModule

from .snaps.clean_charges import clean_charges
from .snaps.extract_charges import extract_charges

# Make TypeVars for all schemas
StripeCharge = TypeVar("StripeCharge")
StripeChargeRaw = TypeVar("StripeChargeRaw")

module = SnapflowModule(
    "stripe",
    py_module_path=__file__,
    py_module_name=__name__,
    schemas=["schemas/stripe_charge.yml", "schemas/stripe_charge_raw.yml"],
    snaps=[extract_charges, clean_charges],
)
module.export()
