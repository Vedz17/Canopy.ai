from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    document_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    topic: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chunk_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    page: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1024),
        nullable=True,
    )

    # Python attribute is meta_data because "metadata"
    # is reserved by SQLAlchemy's DeclarativeBase.
    # The actual PostgreSQL column remains named "metadata".
    meta_data: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        default=dict,
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_document_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    document: Mapped["Document"] = relationship(
        back_populates="chunks",
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    conversation_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    environmental_profile: Mapped["EnvironmentalProfile | None"] = relationship(
        back_populates="conversation",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages",
    )


class EnvironmentalProfile(Base):
    __tablename__ = "environmental_profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # ============================================================
    # TYPED ENVIRONMENTAL CONTROL PLANE
    # ============================================================

    soil_ph: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    soil_organic_carbon: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    soil_moisture: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    temperature: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    annual_rainfall_mm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    water_availability: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    species_richness: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    habitat_diversity: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    habitat_fragmentation: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    land_use: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    pollution: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    deforestation: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ============================================================
    # PROVENANCE REGISTRY
    # ============================================================

    # Stores provenance, confidence and unit information
    # for the typed environmental fields above.
    #
    # Example:
    # {
    #     "soil_ph": {
    #         "provenance": "USER_PROVIDED",
    #         "confidence": 0.95,
    #         "unit": null
    #     },
    #     "annual_rainfall_mm": {
    #         "provenance": "DATASET_ESTIMATE",
    #         "confidence": 0.80,
    #         "unit": "mm/year"
    #     }
    # }
    metric_provenance: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # ============================================================
    # FLEXIBLE / EXTENDED ENVIRONMENTAL CONTEXT
    # ============================================================

    extra_metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # ============================================================
    # SPATIAL CONTEXT
    # ============================================================

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ============================================================
    # TIMESTAMPS
    # ============================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="environmental_profile",
    )


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    intervention_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    target_metrics: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    conditions: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    time_horizon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    evidence_links: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    constraints: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    recommendation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    why: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    affected_metrics: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    time_horizon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    confidence: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    evidence: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    reasoning_trace: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )