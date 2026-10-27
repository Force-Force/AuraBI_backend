import uuid

import pytest

from app.api.v1.analysis import TraceStore
from app.api.v1.insights import generate_insights


@pytest.mark.asyncio
async def test_generate_insights_returns_uiop_payload(monkeypatch):
    async def fake_get_pipeline_or_404(db, pipeline_id):
        return type("Pipeline", (), {"architecture_design": {}})()

    monkeypatch.setattr("app.api.v1.insights.get_pipeline_or_404", fake_get_pipeline_or_404)

    response = await generate_insights(
        pipeline_id=uuid.uuid4(),
        body={"prompt": "Revenue trend by month", "domains": ["sales"]},
        db=None,
    )

    assert response["reply"]
    assert response["uiop"]["protocol"] == "uiop"
    assert response["uiop"]["version"] == "1.0"
    assert response["uiop"]["operations"][0]["op"] == "insight.set_summary"
    assert response["summaryCards"][0]["label"]


def test_trace_store_persists_records_to_disk(tmp_path):
    store = TraceStore(path=tmp_path / "agent_traces.jsonl")
    record = {"request_id": "trace-123", "response": "hello", "trace": {"intent": {"intent": "summary"}}}

    store.save(record)
    reloaded = store.get("trace-123")

    assert reloaded["response"] == "hello"
    assert reloaded["request_id"] == "trace-123"
