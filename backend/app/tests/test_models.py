import pytest
from pydantic import ValidationError

from app.schemas import EmployeeCreate


VALID_PAYLOAD = {
    "full_name": "Jane Doe",
    "email": "jane.doe@example.com",
    "job_title": "Software Engineer",
    "department": "Engineering",
    "country": "India",
    "salary": 120000.00,
    "currency": "INR",
    "employment_type": "Full-time",
    "hire_date": "2024-03-15",
}


def test_valid_employee_creation():
    employee = EmployeeCreate(**VALID_PAYLOAD)
    assert employee.full_name == "Jane Doe"
    assert employee.email == "jane.doe@example.com"
    assert employee.salary == 120000.00
    assert employee.currency == "INR"
    assert employee.employment_type == "Full-time"


def test_empty_full_name_raises():
    payload = {**VALID_PAYLOAD, "full_name": ""}
    with pytest.raises(ValidationError):
        EmployeeCreate(**payload)


def test_negative_salary_raises():
    payload = {**VALID_PAYLOAD, "salary": -500.00}
    with pytest.raises(ValidationError):
        EmployeeCreate(**payload)


@pytest.mark.parametrize("currency", ["JPY", "CNY", "BTC", "", "usd", "USDT"])
def test_invalid_currency_raises(currency):
    payload = {**VALID_PAYLOAD, "currency": currency}
    with pytest.raises(ValidationError):
        EmployeeCreate(**payload)


@pytest.mark.parametrize("employment_type", ["Freelance", "Volunteer", "", "full-time", "INTERN"])
def test_invalid_employment_type_raises(employment_type):
    payload = {**VALID_PAYLOAD, "employment_type": employment_type}
    with pytest.raises(ValidationError):
        EmployeeCreate(**payload)


@pytest.mark.parametrize("hire_date", ["15-03-2024", "2024/03/15", "March 15 2024", "20240315", "not-a-date"])
def test_invalid_hire_date_format_raises(hire_date):
    payload = {**VALID_PAYLOAD, "hire_date": hire_date}
    with pytest.raises(ValidationError):
        EmployeeCreate(**payload)
