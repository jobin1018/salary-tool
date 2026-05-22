import math
from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import distinct
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
    sort_by: str = "id",
    sort_order: str = "asc",
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
