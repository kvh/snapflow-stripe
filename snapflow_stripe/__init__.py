from snapflow import SnapflowModule

from .pipes.extract_stripe_charges import extract_charges
from .pipes.clean_charges import clean_charges


module = SnapflowModule(
    "stripe",
    py_module_path=__file__,
    py_module_name=__name__,
    schemas=["schemas/stripe_charge.yml", "schemas/stripe_charge_raw.yml"],
    pipes=[extract_charges, clean_charges],
)
module.export()
