from pprint import pprint

from dags import Environment
from dags.core.graph import Graph
from dags.testing.utils import get_tmp_sqlite_db_url


def test_stripe(api_key: str):
    import dags_stripe

    env = Environment(metadata_storage="sqlite://")
    g = Graph(env)
    s = env.add_storage(get_tmp_sqlite_db_url())
    env.add_module(dags_stripe)
    # Initial graph
    g.add_node(
        "stripe_charges",
        "stripe.extract_charges",
        config={"api_key": api_key},
    )
    output = env.produce(g, "stripe_charges", target_storage=s)
    records = output.as_records_list()
    pprint(records)


if __name__ == "__main__":
    test_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"
    api_key = input("Enter Stripe API key (default test key): ")
    if not api_key:
        api_key = test_key
    test_stripe(api_key)