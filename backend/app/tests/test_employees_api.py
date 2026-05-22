"""
API integration tests for /api/v1/employees.
All tests use a fresh in-memory SQLite DB via the `client` fixture in conftest.py.
These tests FAIL until the routes are implemented in app/main.py.
"""
import pytest

BASE = "/api/v1/employees"

_ALICE = {
    "full_name": "Alice Johnson",
    "email": "alice@example.com",
    "job_title": "Backend Engineer",
    "department": "Engineering",
    "country": "India",
    "salary": 95000.00,
    "currency": "INR",
    "employment_type": "Full-time",
    "hire_date": "2023-06-01",
}

_BOB = {
    "full_name": "Bob Martin",
    "email": "bob@example.com",
    "job_title": "Product Manager",
    "department": "Product",
    "country": "USA",
    "salary": 130000.00,
    "currency": "USD",
    "employment_type": "Full-time",
    "hire_date": "2022-11-15",
}


# ---------------------------------------------------------------------------
# LIST
# ---------------------------------------------------------------------------

async def test_list_employees_returns_200_with_pagination_shape(client):
    r = await client.get(BASE)
    assert r.status_code == 200
    body = r.json()
    for key in ("items", "total", "page", "total_pages"):
        assert key in body, f"missing key: {key}"
    assert isinstance(body["items"], list)
    assert body["total"] == 0
    assert body["items"] == []


async def test_list_employees_reflects_created_records(client):
    await client.post(BASE, json=_ALICE)
    await client.post(BASE, json=_BOB)

    r = await client.get(BASE)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

async def test_create_employee_returns_201_with_body(client):
    r = await client.post(BASE, json=_ALICE)
    assert r.status_code == 201
    body = r.json()
    assert "id" in body
    assert body["email"] == _ALICE["email"]
    assert body["full_name"] == _ALICE["full_name"]
    assert body["job_title"] == _ALICE["job_title"]
    assert body["department"] == _ALICE["department"]
    assert body["country"] == _ALICE["country"]
    assert body["currency"] == _ALICE["currency"]
    assert body["employment_type"] == _ALICE["employment_type"]
    assert body["hire_date"] == _ALICE["hire_date"]


async def test_create_duplicate_email_returns_400_or_409(client):
    await client.post(BASE, json=_ALICE)
    r = await client.post(BASE, json=_ALICE)
    assert r.status_code in (400, 409)


# ---------------------------------------------------------------------------
# GET BY ID
# ---------------------------------------------------------------------------

async def test_get_employee_by_id_returns_200(client):
    created = (await client.post(BASE, json=_ALICE)).json()
    emp_id = created["id"]

    r = await client.get(f"{BASE}/{emp_id}")
    assert r.status_code == 200
    assert r.json()["id"] == emp_id
    assert r.json()["email"] == _ALICE["email"]


async def test_get_employee_unknown_id_returns_404(client):
    r = await client.get(f"{BASE}/99999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PATCH
# ---------------------------------------------------------------------------

async def test_patch_updates_only_provided_fields(client):
    created = (await client.post(BASE, json=_ALICE)).json()
    emp_id = created["id"]

    r = await client.patch(f"{BASE}/{emp_id}", json={"job_title": "Staff Engineer", "salary": 110000})
    assert r.status_code == 200
    body = r.json()
    assert body["job_title"] == "Staff Engineer"
    assert body["salary"] == 110000
    # untouched fields stay the same
    assert body["full_name"] == _ALICE["full_name"]
    assert body["email"] == _ALICE["email"]
    assert body["department"] == _ALICE["department"]


async def test_patch_unknown_id_returns_404(client):
    r = await client.patch(f"{BASE}/99999", json={"job_title": "Ghost"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

async def test_delete_employee_returns_204(client):
    created = (await client.post(BASE, json=_ALICE)).json()
    emp_id = created["id"]

    r = await client.delete(f"{BASE}/{emp_id}")
    assert r.status_code == 204

    # confirm gone
    r2 = await client.get(f"{BASE}/{emp_id}")
    assert r2.status_code == 404


async def test_delete_unknown_id_returns_404(client):
    r = await client.delete(f"{BASE}/99999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# FILTERS via query params
# ---------------------------------------------------------------------------

async def test_search_by_name_filters_results(client):
    await client.post(BASE, json=_ALICE)   # "Alice Johnson"
    await client.post(BASE, json=_BOB)     # "Bob Martin"

    r = await client.get(f"{BASE}?search=alice")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["email"] == _ALICE["email"]


async def test_filter_by_country(client):
    await client.post(BASE, json=_ALICE)   # India
    await client.post(BASE, json=_BOB)     # USA

    r = await client.get(f"{BASE}?country=India")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert all(emp["country"] == "India" for emp in body["items"])


async def test_search_and_country_filter_combined(client):
    await client.post(BASE, json=_ALICE)
    await client.post(BASE, json=_BOB)

    r = await client.get(f"{BASE}?search=bob&country=India")
    assert r.status_code == 200
    assert r.json()["total"] == 0


# ---------------------------------------------------------------------------
# /filters meta-endpoint
# ---------------------------------------------------------------------------

async def test_filters_endpoint_returns_distinct_countries_and_departments(client):
    await client.post(BASE, json=_ALICE)
    await client.post(BASE, json=_BOB)

    # NOTE: /filters must be registered BEFORE /{id} in the router
    # so FastAPI doesn't treat the literal "filters" as an integer id.
    r = await client.get(f"{BASE}/filters")
    assert r.status_code == 200
    body = r.json()
    assert "countries" in body
    assert "departments" in body
    assert set(body["countries"]) == {"India", "USA"}
    assert set(body["departments"]) == {"Engineering", "Product"}


async def test_filters_endpoint_empty_db(client):
    r = await client.get(f"{BASE}/filters")
    assert r.status_code == 200
    body = r.json()
    assert body["countries"] == []
    assert body["departments"] == []
