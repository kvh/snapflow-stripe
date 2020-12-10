Stripe module for the [snapflow](https://github.com/kvh/snapflow) framework.

#### Install

`pip install snapflow-stripe` or `poetry add snapflow-stripe`

#### Example

```python
from snapflow import Graph, produce
import snapflow_stripe

g = Graph()

raw_charges = g.create_node(
    "stripe.extract_charges",
    config={"api_key": api_key},
)
stripe_charges = g.create_node(
    "stripe.clean_charges", upstream=raw_charges
)
output = produce(
    stripe_charges, g, node_timelimit_seconds=5, modules=[snapflow_stripe]
)
records = output.as_records_list()
```
