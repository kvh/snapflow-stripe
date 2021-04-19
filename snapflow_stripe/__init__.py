from typing import TypeVar

from snapflow import SnapflowModule

from .functions.clean_charges import clean_charges
from .functions.import_charges import import_charges

# Make TypeVars for all schemas
StripeCharge = TypeVar("StripeCharge")
StripeChargeRaw = TypeVar("StripeChargeRaw")

module = SnapflowModule(
    "stripe",
    py_module_path=__file__,
    py_module_name=__name__,
)
module.add_function(clean_charges)
module.add_function(import_charges)
