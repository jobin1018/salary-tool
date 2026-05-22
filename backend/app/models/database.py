from sqlalchemy import Column, Date, DateTime, Index, Integer, Numeric, String
from sqlalchemy.sql import func

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    job_title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    country = Column(String, nullable=False)
    salary = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    employment_type = Column(String, nullable=False)
    hire_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_employees_country_job_title", "country", "job_title"),
    )
