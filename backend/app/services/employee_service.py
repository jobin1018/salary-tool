import math
import statistics
from datetime import date
from typing import Dict, List, Optional, Tuple

from sqlalchemy import distinct, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.database import Employee
from app.models.schemas import EmployeeCreate, EmployeeUpdate

_SORTABLE = {
    "id": Employee.id,
    "full_name": Employee.full_name,
    "salary": Employee.salary,
    "hire_date": Employee.hire_date,
    "created_at": Employee.created_at,
}


def get_employee(db: Session, emp_id: int) -> Optional[Employee]:
    return db.query(Employee).filter(Employee.id == emp_id).first()


def get_employees(
    db: Session,
    search: Optional[str] = None,
    country: Optional[str] = None,
    department: Optional[str] = None,
    employment_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "hire_date",
    sort_order: str = "desc",
) -> Tuple[List[Employee], int, int]:
    q = db.query(Employee)

    if search:
        q = q.filter(Employee.full_name.ilike(f"%{search}%"))
    if country:
        q = q.filter(Employee.country == country)
    if department:
        q = q.filter(Employee.department == department)
    if employment_type:
        q = q.filter(Employee.employment_type == employment_type)

    total = q.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    sort_col = _SORTABLE.get(sort_by, Employee.id)
    if sort_order == "desc":
        sort_col = sort_col.desc()
    q = q.order_by(sort_col)

    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total, total_pages


def create_employee(db: Session, data: EmployeeCreate) -> Employee:
    emp = Employee(
        full_name=data.full_name,
        email=str(data.email),
        job_title=data.job_title,
        department=data.department,
        country=data.country,
        salary=data.salary,
        currency=data.currency,
        employment_type=data.employment_type,
        hire_date=date.fromisoformat(data.hire_date),
    )
    db.add(emp)
    try:
        db.commit()
        db.refresh(emp)
    except IntegrityError:
        db.rollback()
        raise
    return emp


def update_employee(db: Session, emp_id: int, data: EmployeeUpdate) -> Optional[Employee]:
    emp = get_employee(db, emp_id)
    if emp is None:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "hire_date" and value is not None:
            value = date.fromisoformat(value)
        setattr(emp, field, value)

    db.commit()
    db.refresh(emp)
    return emp


def delete_employee(db: Session, emp_id: int) -> bool:
    emp = get_employee(db, emp_id)
    if emp is None:
        return False
    db.delete(emp)
    db.commit()
    return True


def get_distinct_countries(db: Session) -> List[str]:
    rows = db.query(distinct(Employee.country)).order_by(Employee.country).all()
    return [r[0] for r in rows]


def get_distinct_departments(db: Session) -> List[str]:
    rows = db.query(distinct(Employee.department)).order_by(Employee.department).all()
    return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# Insight helpers
# ---------------------------------------------------------------------------

def _compute_stats(
    db: Session,
    country: str,
    job_title: Optional[str] = None,
) -> Optional[Dict]:
    """SQL aggregates + Python median for a country (optionally filtered by job_title)."""
    q = db.query(Employee).filter(Employee.country == country)
    if job_title is not None:
        q = q.filter(Employee.job_title == job_title)

    # with_entities() returns a new query, leaving q's filters intact for reuse.
    count, min_sal, max_sal, avg_sal = q.with_entities(
        func.count(Employee.id),
        func.min(Employee.salary),
        func.max(Employee.salary),
        func.avg(Employee.salary),
    ).one()

    if not count:
        return None

    salaries = [float(r[0]) for r in q.with_entities(Employee.salary).all()]
    return {
        "count": int(count),
        "min_salary": float(min_sal),
        "max_salary": float(max_sal),
        "avg_salary": float(avg_sal),
        "median_salary": float(statistics.median(salaries)),
    }


def get_country_salary_stats(db: Session, country: str) -> Optional[Dict]:
    return _compute_stats(db, country)


def get_job_title_stats_in_country(
    db: Session, country: str, job_title: str
) -> Optional[Dict]:
    return _compute_stats(db, country, job_title)


def get_all_job_titles_in_country(db: Session, country: str) -> Optional[List[str]]:
    exists = db.query(Employee.id).filter(Employee.country == country).first()
    if not exists:
        return None
    rows = (
        db.query(distinct(Employee.job_title))
        .filter(Employee.country == country)
        .order_by(Employee.job_title)
        .all()
    )
    return [r[0] for r in rows]


def get_insights_summary(db: Session) -> Dict:
    total, g_min, g_max, g_avg = db.query(
        func.count(Employee.id),
        func.min(Employee.salary),
        func.max(Employee.salary),
        func.avg(Employee.salary),
    ).one()

    country_rows = (
        db.query(Employee.country, func.count(Employee.id), func.avg(Employee.salary))
        .group_by(Employee.country)
        .order_by(Employee.country)
        .all()
    )

    dept_rows = (
        db.query(Employee.department, func.count(Employee.id), func.avg(Employee.salary))
        .group_by(Employee.department)
        .order_by(Employee.department)
        .all()
    )

    top_earners = (
        db.query(Employee).order_by(Employee.salary.desc()).limit(10).all()
    )

    return {
        "total_employees": int(total) if total else 0,
        "global_avg_salary": float(g_avg) if g_avg is not None else 0.0,
        "global_min_salary": float(g_min) if g_min is not None else 0.0,
        "global_max_salary": float(g_max) if g_max is not None else 0.0,
        "country_breakdown": [
            {"country": r[0], "count": r[1], "avg_salary": float(r[2])}
            for r in country_rows
        ],
        "department_breakdown": [
            {"department": r[0], "count": r[1], "avg_salary": float(r[2])}
            for r in dept_rows
        ],
        "top_earners": [
            {
                "id": e.id,
                "full_name": e.full_name,
                "email": e.email,
                "job_title": e.job_title,
                "department": e.department,
                "country": e.country,
                "salary": float(e.salary),
                "currency": e.currency,
                "employment_type": e.employment_type,
                "hire_date": e.hire_date.isoformat() if e.hire_date else None,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            }
            for e in top_earners
        ],
    }
