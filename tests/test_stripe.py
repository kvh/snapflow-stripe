from pprint import pprint

import pytest
from dcp.storage.database.utils import get_tmp_sqlite_db_url
from snapflow import Environment, DataspaceCfg, GraphCfg

TEST_API_KEY = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"


@pytest.mark.parametrize("api_key", [(TEST_API_KEY)])
def test_stripe(api_key):
    run_stripe_test(api_key)


def run_stripe_test(api_key: str):
    from snapflow_stripe import module as stripe

    if not api_key:
        api_key = TEST_API_KEY
    storage = get_tmp_sqlite_db_url()
    env = Environment(DataspaceCfg(metadata_storage="sqlite://", storages=[storage]))
    env.add_module(stripe)

    # Initial graph
    raw_charges = GraphCfg(
        key="import_charges",
        function="stripe.import_charges",
        params={"api_key": api_key},
    )
    clean_charges = GraphCfg(
        key="clean_charges", function="stripe.clean_charges", input="import_charges"
    )
    g = GraphCfg(nodes=[raw_charges, clean_charges])
    results = env.produce(
        clean_charges.key, g, target_storage=storage, execution_timelimit_seconds=1
    )
    records = results[0].stdout().as_records()
    assert len(records) >= 100
    assert records[0]["amount"] > 0


if __name__ == "__main__":
    api_key = input("Enter Stripe API key (default test key): ")
    test_stripe(api_key)
