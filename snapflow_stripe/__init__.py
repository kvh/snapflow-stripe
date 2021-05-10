from typing import TypeVar

from snapflow import SnapflowModule

from .functions.import_subscriptions import import_subscriptions
from .functions.clean_charges import clean_charges
from .functions.import_charges import import_charges
from .functions.import_refunds import import_refunds

# Make TypeVars for all schemas
StripeCharge = TypeVar("StripeCharge")
StripeChargeRaw = TypeVar("StripeChargeRaw")
StripeRefundRaw = TypeVar("StripeRefundRaw")
StripeSubscriptionRaw = TypeVar("StripeSubscriptionRaw")

module = SnapflowModule("stripe", py_module_path=__file__, py_module_name=__name__,)
module.add_function(clean_charges)
module.add_function(import_charges)
module.add_function(import_refunds)
module.add_function(import_subscriptions)
