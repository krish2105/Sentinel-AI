"""Tests for Phase 3: rate limiting, PDF export, multi-turn attacks, comparison."""
import pytest

from app.core.security import RateLimiter


# --- Rate limiting ----------------------------------------------------------
@pytest.mark.asyncio
async def test_rate_limiter_in_memory_window():
    rl = RateLimiter(per_minute=3)  # no redis_url -> in-memory
    assert [await rl.allow("ip") for _ in range(3)] == [True, True, True]
    assert await rl.allow("ip") is False  # 4th in the same window blocked
    assert await rl.allow("other-ip") is True  # per-key isolation


@pytest.mark.asyncio
async def test_rate_limiter_bad_redis_falls_back():
    # An unreachable Redis URL must degrade to in-memory, never raise/500.
    rl = RateLimiter(per_minute=2, redis_url="redis://127.0.0.1:6390/0")
    assert await rl.allow("k") is True
    assert await rl.allow("k") is True
    assert await rl.allow("k") is False


# --- Multi-turn attacks -----------------------------------------------------
@pytest.mark.asyncio
async def test_multi_turn_jailbreak_run(client):
    t = await client.post(
        "/targets", json={"name": "Chatty", "system_prompt": "You are a bot.", "tools": []}
    )
    run = await client.post(
        "/runs", json={"target_id": t.json()["id"], "selected_categories": ["jailbreak"]}
    )
    run_id = run.json()["id"]
    async with client.stream("GET", f"/runs/{run_id}/stream") as s:
        async for line in s.aiter_lines():
            if "run_completed" in line:
                break
    attacks = (await client.get(f"/runs/{run_id}/attacks")).json()
    assert attacks
    # jailbreak is a multi-turn crescendo (>1 turn).
    assert all(a["turns"] > 1 for a in attacks)
    assert "[turn 1]" in attacks[0]["payload"]


def test_attack_library_has_richer_banks():
    from app.llm.mock_engine import _ATTACK_BANK

    # Each category now carries multiple distinct payloads.
    assert all(len(v) >= 3 for v in _ATTACK_BANK.values())


# --- Styled PDF export ------------------------------------------------------
@pytest.mark.asyncio
async def test_pdf_export_returns_pdf(client):
    t = await client.post(
        "/targets", json={"name": "PDF Bot", "system_prompt": "You are a bot.", "tools": []}
    )
    run = await client.post(
        "/runs", json={"target_id": t.json()["id"], "selected_categories": ["direct_injection"]}
    )
    run_id = run.json()["id"]
    async with client.stream("GET", f"/runs/{run_id}/stream") as s:
        async for line in s.aiter_lines():
            if "run_completed" in line:
                break
    resp = await client.get(f"/reports/{run_id}/pdf")
    assert resp.status_code == 200
    # reportlab is installed in the test env -> a real PDF, not the HTML fallback.
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:5] == b"%PDF-"


# --- Run-to-run comparison --------------------------------------------------
@pytest.mark.asyncio
async def test_compare_first_run_is_baseline(client):
    t = await client.post(
        "/targets", json={"name": "Baseline", "system_prompt": "You are a bot.", "tools": []}
    )
    run = await client.post(
        "/runs", json={"target_id": t.json()["id"], "selected_categories": ["jailbreak"]}
    )
    run_id = run.json()["id"]
    async with client.stream("GET", f"/runs/{run_id}/stream") as s:
        async for line in s.aiter_lines():
            if "run_completed" in line:
                break
    cmp = (await client.get(f"/runs/{run_id}/compare")).json()
    assert cmp["has_previous"] is False
    assert cmp["posture_delta"] is None


@pytest.mark.asyncio
async def test_compare_second_run_has_deltas(client):
    t = await client.post(
        "/targets", json={"name": "Trend", "system_prompt": "You are a bot.", "tools": []}
    )
    tid = t.json()["id"]

    async def do_run():
        r = await client.post(
            "/runs", json={"target_id": tid, "selected_categories": ["direct_injection"]}
        )
        rid = r.json()["id"]
        async with client.stream("GET", f"/runs/{rid}/stream") as s:
            async for line in s.aiter_lines():
                if "run_completed" in line:
                    break
        return rid

    await do_run()
    second = await do_run()
    cmp = (await client.get(f"/runs/{second}/compare")).json()
    assert cmp["has_previous"] is True
    assert cmp["previous_run_id"] is not None
    assert cmp["posture_delta"] is not None
    assert isinstance(cmp["regressed_categories"], list)
