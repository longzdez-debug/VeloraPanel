from velora.account_pool import AccountPool, FarmStatus


class A:
    def __init__(self, id, enabled=True):
        self.id = id
        self.enabled = enabled


def test_pool_selects_unfarmed_accounts():
    pool = AccountPool([A("a"), A("b"), A("c", False)])
    pool.mark("a", FarmStatus.COMPLETED)
    assert [x.id for x in pool.select_unfarmed()] == ["b"]


def test_pool_select_limit():
    pool = AccountPool([A("a"), A("b"), A("c")])
    assert len(pool.select(limit=2)) == 2
