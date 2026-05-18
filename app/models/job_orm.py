import uuid
from datetime import datetime

from sqlalchemy import ARRAY, JSON, DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    department: Mapped[str | None] = mapped_column(String(256), nullable=True)
    company: Mapped[str | None] = mapped_column(String(256), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    skills: Mapped[list[str] | None] = mapped_column(ARRAY(String(64)), nullable=True)
    seniority_level: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)

    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_job_provider_external"),
        Index("ix_jobs_active_company", "is_active", "company"),
        Index("ix_jobs_provider_company", "provider", "company"),
        Index("ix_jobs_location", "location"),
        Index("ix_jobs_department", "department"),
        Index("ix_jobs_skills", "skills", postgresql_using="gin"),
        Index("ix_jobs_location_department", "location", "department"),
        Index("ix_jobs_department_seniority", "department", "seniority_level"),
    )
