from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import EmployeeCreate, EmployeeRead, EmployeeUpdate, PaginatedEmployees
from app.services import employee_service as svc

router = APIRouter(prefix="/api/v1/employees", tags=["employees"])


# /filters MUST be declared before /{emp_id} so FastAPI doesn't try to
# coerce the literal string "filters" to an integer path parameter.
@router.get("/filters")
def get_filters(db: Session = Depends(get_db)):
    return {
        "countries": svc.get_distinct_countries(db),
        "departments": svc.get_distinct_departments(db),
    }


@router.get("", response_model=PaginatedEmployees)
def list_employees(
    search: Optional[str] = Query(default=None),
    country: Optional[str] = Query(default=None),
    department: Optional[str] = Query(default=None),
    employment_type: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="id"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    items, total, total_pages = svc.get_employees(
        db,
        search=search,
        country=country,
        department=department,
        employment_type=employment_type,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return PaginatedEmployees(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    try:
        return svc.create_employee(db, payload)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")


@router.get("/{emp_id}", response_model=EmployeeRead)
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = svc.get_employee(db, emp_id)
    if emp is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.patch("/{emp_id}", response_model=EmployeeRead)
def patch_employee(emp_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    emp = svc.update_employee(db, emp_id, payload)
    if emp is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.delete("/{emp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    deleted = svc.delete_employee(db, emp_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Employee not found")
