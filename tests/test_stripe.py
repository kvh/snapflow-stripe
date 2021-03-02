from pprint import pprint

import pytest
from snapflow import Environment
from snapflow.core.graph import Graph
from snapflow.testing.utils import get_tmp_sqlite_db_url

TEST_API_KEY = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"


@pytest.mark.parametrize("api_key", [(TEST_API_KEY)])
def test_stripe(api_key):
    run_stripe_test(api_key)

def run_stripe_test(api_key: str):
    import snapflow_stripe

    if not api_key:
        api_key = TEST_API_KEY
    env = Environment(metadata_storage="sqlite://")
    g = Graph(env)
    s = env.add_storage(get_tmp_sqlite_db_url())
    env.add_module(snapflow_stripe)

    # Initial graph
    raw_charges = g.create_node(
        "stripe.extract_charges",
        params={"api_key": api_key},
    )
    clean_charges = g.create_node("stripe.clean_charges", upstream=raw_charges)
    output = env.produce(
        clean_charges, g, target_storage=s, node_timelimit_seconds=0.01
    )
    records = output.as_records()
    assert len(records) >= 100
    assert records[0]["amount"] > 0


if __name__ == "__main__":
    api_key = input("Enter Stripe API key (default test key): ")
    test_stripe(api_key)
