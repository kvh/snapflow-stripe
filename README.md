Stripe module for the [snapflow](https://github.com/kvh/snapflow) framework.

#### Install

`pip install snapflow-stripe` or `poetry add snapflow-stripe`

#### Example

```python
from snapflow import Graph, produce
from snapflow_stripe import module as stripe

g = Graph()

raw_charges = g.create_node(
    "stripe.import_charges",
    params={"api_key": api_key},
)
stripe_charges = g.create_node(
    "stripe.clean_charges", upstream=raw_charges
)
blocks = produce(
    stripe_charges, g, execution_timelimit_seconds=5, modules=[stripe]
)
records = blocks[0].as_records()
```
