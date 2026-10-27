from datetime import datetime, timedelta, timezone

from app.models.pipeline_run import PipelineRun
from app.models.edge import Edge
from app.schemas.edge import EdgeCreate, EdgeRead
from app.schemas.execution import PipelineRunEventRead, PipelineRunRead


def test_edge_contract_supports_column_lineage() -> None:
    edge = EdgeCreate(
        source_node_id="11111111-1111-4111-8111-111111111111",
        target_node_id="22222222-2222-4222-8222-222222222222",
        from_column="customer_id",
        to_column="customer_key",
        source_handle="right-center",
        target_handle="left-center",
        relationship="foreign_key",
        metadata={"fkRefTable": "dim_customer_360"},
    )

    assert edge.from_column == "customer_id"
    assert edge.to_column == "customer_key"
    assert edge.relationship == "foreign_key"

    read = EdgeRead.model_validate(
        {
            "id": "33333333-3333-4333-8333-333333333333",
            "source": "11111111-1111-4111-8111-111111111111",
            "target": "22222222-2222-4222-8222-222222222222",
            "from_column": "customer_id",
            "to_column": "customer_key",
            "source_handle": "right-center",
            "target_handle": "left-center",
            "relationship": "foreign_key",
            "metadata": {"fkRefTable": "dim_customer_360"},
        }
    )
    assert read.relationship == "foreign_key"
    assert read.metadata["fkRefTable"] == "dim_customer_360"


def test_run_contract_includes_telemetry() -> None:
    started = datetime.now(timezone.utc)
    ended = started + timedelta(minutes=2, seconds=17)

    run = PipelineRun(
        id="44444444-4444-4444-8444-444444444444",
        pipeline_id="55555555-5555-4555-8555-555555555555",
        status="COMPLETED",
        run_number=7,
        duration_seconds=137.0,
        records_processed=12000,
        nodes_executed=4,
        total_nodes=6,
        started_at=started,
        completed_at=ended,
        context={"node_order": ["a", "b"]},
    )

    payload = PipelineRunRead.model_validate(run)
    assert payload.run_number == 7
    assert payload.duration_seconds == 137.0
    assert payload.total_nodes == 6
    assert payload.nodes_executed == 4

    event = PipelineRunEventRead.model_validate(
        {
            "id": "66666666-6666-4666-8666-666666666666",
            "run_id": "44444444-4444-4444-8444-444444444444",
            "pipeline_id": "55555555-5555-4555-8555-555555555555",
            "event_type": "STEP_COMPLETED",
            "message_md": "Completed node", 
            "payload": {},
            "created_at": started,
            "phase": "execution",
            "status": "SUCCESS",
            "duration_ms": 250,
        }
    )
    assert event.status == "SUCCESS"
    assert event.phase == "execution"
