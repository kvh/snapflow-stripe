## Snapflow module for Stripe

[https://github.com/kvh/snapflow](https://github.com/kvh/snapflow)

```python
from snapflow import Graph, produce
import snapflow_stripe

g = Graph()

g.create_node(
    "stripe_charges_raw",
    "stripe.extract_charges",
    config={"api_key": api_key},
)
stripe_charges = g.create_node(
    "stripe_charges", "stripe.clean_charges", upstream="stripe_charges_raw"
)
output = produce(
    stripe_charges, g, node_timelimit_seconds=5, modules=[snapflow_stripe]
)
records = output.as_records_list()
```
