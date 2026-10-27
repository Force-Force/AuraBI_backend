from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EdgeCreate(BaseModel):
    source_node_id: UUID
    target_node_id: UUID
    from_column: str | None = None
    to_column: str | None = None
    source_handle: str | None = None
    target_handle: str | None = None
    relationship: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EdgeRead(BaseModel):
    id: UUID
    source: UUID
    target: UUID
    from_column: str | None = None
    to_column: str | None = None
    source_handle: str | None = None
    target_handle: str | None = None
    relationship: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}
