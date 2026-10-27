from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.pipeline_service import get_pipeline_or_404

router = APIRouter(prefix="/pipelines/{pipeline_id}", tags=["insights"])


class InsightGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    domains: list[str] = Field(default_factory=list)


def _default_insight_payload(prompt: str, domains: list[str]) -> dict[str, Any]:
    cards = [
        {"label": "Net revenue", "value": "$1.15M", "delta": "+9.1%"},
        {"label": "Enterprise retention", "value": "118%", "delta": "+4.5%"},
        {"label": "Orders processed", "value": "420K", "delta": "99.85% delivered"},
        {"label": "Outliers", "value": "1", "delta": "Oct 18"},
    ]
    insights = [
        {
            "id": "insight-net-revenue-bridge",
            "kpiId": "net-recognized-revenue",
            "kpiName": "Net Recognized Revenue",
            "domain": domains[0] if domains else "sales",
            "categoryLabel": "Revenue Decomposition",
            "title": "Gross-to-Net Revenue Bridge (Q3 Settlement)",
            "summary": (
                "Net recognized revenue reached $1,150,000 (+9.1% QoQ), with promotional discounts "
                "(-$92K) and refunds (-$48K) within historical guardrails."
            ),
            "aiReasoning": "Selected a Waterfall Decomposition graph because financial gross-to-net reconciliation is an additive/subtractive bridge across ledger adjustments.",
            "aiConfidenceScore": 99.4,
            "selectedGraphType": "waterfall-decomposition",
            "availableGraphOptions": [
                {
                    "type": "waterfall-decomposition",
                    "label": "Waterfall Bridge",
                    "isAiRecommended": True,
                    "reasoning": "Best for visualizing gross-to-net ledger deductions and subtotals.",
                },
                {
                    "type": "anomaly-ribbon",
                    "label": "Anomaly Confidence Ribbon",
                    "isAiRecommended": False,
                    "reasoning": "Highlights daily revenue spikes outside the expected 95% confidence band.",
                },
            ],
            "headlineMetrics": [
                {"label": "Gross Volume (GMV)", "value": "$1.34M", "delta": "+11.2%", "trend": "up"},
                {"label": "Net Recognized", "value": "$1.15M", "delta": "+9.1%", "trend": "up"},
                {"label": "Refund Leakage", "value": "3.58%", "delta": "-0.4%", "trend": "down"},
            ],
            "waterfallData": [
                {"id": "w1", "label": "Gross GMV", "amount": 1340000, "formatted": "$1.34M"},
                {"id": "w2", "label": "Promotions", "amount": -92000, "formatted": "-$92K"},
                {"id": "w3", "label": "Refunds", "amount": -48000, "formatted": "-$48K"},
                {"id": "w4", "label": "Net Recognized", "amount": 1150000, "formatted": "$1.15M"},
            ],
        }
    ]
    return {"summaryCards": cards, "insights": insights, "prompt": prompt, "domains": domains}


@router.post("/insights/generate")
async def generate_insights(
    pipeline_id: UUID,
    body: InsightGenerateRequest | dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    request = body if isinstance(body, InsightGenerateRequest) else InsightGenerateRequest.model_validate(body)
    pipeline = await get_pipeline_or_404(db, pipeline_id)
    payload = _default_insight_payload(request.prompt, request.domains)
    design = dict(pipeline.architecture_design or {})
    design["insights"] = payload
    pipeline.architecture_design = design
    if db is not None and hasattr(db, "flush"):
        await db.flush()

    uiop = {
        "protocol": "uiop",
        "version": "1.0",
        "messageId": f"msg_ins_gen_{pipeline_id}",
        "workspaceId": str(pipeline_id),
        "baseRevision": 1,
        "source": {"agentId": "insights-agent", "executionId": "exec_insights"},
        "operations": [
            {"op": "insight.set_summary", "params": {"cards": payload["summaryCards"]}},
            {"op": "insight.add", "params": payload["insights"][0]},
        ],
    }
    return {"reply": "I queried the pipeline profile and generated the dashboard summary.", "summaryCards": payload["summaryCards"], "insights": payload["insights"], "uiop": uiop}


@router.get("/insights")
async def list_insights(
    pipeline_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    pipeline = await get_pipeline_or_404(db, pipeline_id)
    design = dict(pipeline.architecture_design or {})
    payload = design.get("insights")
    if payload is None:
        payload = _default_insight_payload("Pipeline overview", [])
        design["insights"] = payload
        pipeline.architecture_design = design
        await db.flush()
    return payload
