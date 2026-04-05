from lib.db import get_db, insert_invocation, get_invocation, list_invocations, update_cost, get_stats, recreate_db


def _make_db():
    return get_db(":memory:")


def test_init_tables():
    db = _make_db()
    rows = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    names = [r["name"] for r in rows]
    assert "invocations" in names


def test_insert_and_get():
    db = _make_db()
    inv_id = insert_invocation(
        db,
        prompt_topic="test",
        prompt_name="hello",
        prompt_version="abc12345",
        full_prompt="Say hello",
        model_id="openai/gpt-4o",
        temperature=0.7,
        max_tokens=100,
        full_response="Hello!",
        prompt_tokens=5,
        completion_tokens=2,
        total_tokens=7,
        latency_ms=200,
        status="success",
    )
    assert inv_id >= 1

    inv = get_invocation(db, inv_id)
    assert inv is not None
    assert inv["prompt_topic"] == "test"
    assert inv["prompt_name"] == "hello"
    assert inv["model_id"] == "openai/gpt-4o"
    assert inv["full_response"] == "Hello!"
    assert inv["total_tokens"] == 7


def test_list_invocations_filter():
    db = _make_db()
    insert_invocation(db, prompt_topic="a", prompt_name="x", full_prompt="p1", model_id="m1")
    insert_invocation(db, prompt_topic="b", prompt_name="y", full_prompt="p2", model_id="m2")
    insert_invocation(db, prompt_topic="a", prompt_name="z", full_prompt="p3", model_id="m1")

    all_inv = list_invocations(db)
    assert len(all_inv) == 3

    filtered = list_invocations(db, prompt_topic="a")
    assert len(filtered) == 2

    filtered_model = list_invocations(db, model_id="m2")
    assert len(filtered_model) == 1


def test_update_cost():
    db = _make_db()
    inv_id = insert_invocation(db, prompt_topic="t", prompt_name="n", full_prompt="p", model_id="m")
    inv = get_invocation(db, inv_id)
    assert inv["cost_usd"] is None

    update_cost(db, inv_id, 0.0042)
    inv = get_invocation(db, inv_id)
    assert abs(inv["cost_usd"] - 0.0042) < 1e-6


def test_get_stats():
    db = _make_db()
    insert_invocation(
        db, prompt_topic="t", prompt_name="n", full_prompt="p", model_id="m1",
        cost_usd=0.01, total_tokens=100,
    )
    insert_invocation(
        db, prompt_topic="t", prompt_name="n2", full_prompt="p2", model_id="m2",
        cost_usd=0.02, total_tokens=200,
    )
    stats = get_stats(db)
    assert stats["total_runs"] == 2
    assert abs(stats["total_cost"] - 0.03) < 1e-6
    assert stats["total_tokens"] == 300
    assert stats["unique_models"] == 2


def test_get_nonexistent():
    db = _make_db()
    assert get_invocation(db, 999) is None


def test_recreate_db():
    db = _make_db()
    insert_invocation(db, prompt_topic="t", prompt_name="n", full_prompt="p", model_id="m")
    assert len(list_invocations(db)) == 1
    recreate_db(db)
    assert len(list_invocations(db)) == 0
