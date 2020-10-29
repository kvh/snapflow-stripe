from dags.core.module import DagsModule

from .pipes.extract_stripe_charges import extract_charges

module = DagsModule(
    "stripe",
    py_module_path=__file__,
    py_module_name=__name__,
    schemas=["schemas/stripe_charge.yml"],
    pipes=[extract_charges],
)
module.export()
