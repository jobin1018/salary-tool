import re
from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

_HIRE_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_hire_date(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    if not _HIRE_DATE_RE.match(v):
        raise ValueError("hire_date must be in YYYY-MM-DD format")
    try:
        date.fromisoformat(v)
    except ValueError:
        raise ValueError("hire_date must be a valid date in YYYY-MM-DD format")
    return v


class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=1)
    email: EmailStr
    job_title: str
    department: str
    country: str
    salary: float = Field(ge=0)
    currency: Literal["USD", "EUR", "GBP", "INR", "AED", "AUD", "CAD", "SGD"]
    employment_type: Literal["Full-time", "Part-time", "Contract", "Intern"]
    hire_date: str

    @field_validator("hire_date")
    @classmethod
    def check_hire_date(cls, v: str) -> str:
        return _validate_hire_date(v)


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1)
    email: Optional[EmailStr] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    country: Optional[str] = None
    salary: Optional[float] = Field(default=None, ge=0)
    currency: Optional[Literal["USD", "EUR", "GBP", "INR", "AED", "AUD", "CAD", "SGD"]] = None
    employment_type: Optional[Literal["Full-time", "Part-time", "Contract", "Intern"]] = None
    hire_date: Optional[str] = None

    @field_validator("hire_date")
    @classmethod
    def check_hire_date(cls, v: Optional[str]) -> Optional[str]:
        return _validate_hire_date(v)


class EmployeeRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    full_name: str
    email: str
    job_title: str
    department: str
    country: str
    salary: float
    currency: str
    employment_type: str
    hire_date: date
    created_at: datetime
    updated_at: datetime


class PaginatedEmployees(BaseModel):
    items: List[EmployeeRead]
    total: int
    page: int
    page_size: int
