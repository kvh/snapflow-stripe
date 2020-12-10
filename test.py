from pprint import pprint

from snapflow import Environment
from snapflow.core.graph import Graph
from snapflow.testing.utils import get_tmp_sqlite_db_url


def test_stripe(api_key: str):
    import snapflow_stripe

    env = Environment(metadata_storage="sqlite://")
    g = Graph(env)
    s = env.add_storage(get_tmp_sqlite_db_url())
    env.add_module(snapflow_stripe)

    # Initial graph
    raw_charges = g.create_node(
        "stripe.extract_charges",
        config={"api_key": api_key},
    )
    clean_charges = g.create_node("stripe.clean_charges", upstream=raw_charges)
    output = env.produce(clean_charges, g, target_storage=s, node_timelimit_seconds=5)
    records = output.as_records_list()
    assert len(records) > 100
    assert records[0]["amount"] == 100


if __name__ == "__main__":
    test_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"
    api_key = input("Enter Stripe API key (default test key): ")
    if not api_key:
        api_key = test_key
    test_stripe(api_key)
