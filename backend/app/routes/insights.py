from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import employee_service as svc

router = APIRouter(prefix="/api/v1/insights", tags=["insights"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return svc.get_insights_summary(db)


@router.get("/country/{country}")
def country_stats(country: str, db: Session = Depends(get_db)):
    stats = svc.get_country_salary_stats(db, country)
    if stats is None:
        raise HTTPException(status_code=404, detail=f"No employees found for country: {country}")
    return stats


@router.get("/country/{country}/job-titles")
def country_job_titles(country: str, db: Session = Depends(get_db)):
    titles = svc.get_all_job_titles_in_country(db, country)
    if titles is None:
        raise HTTPException(status_code=404, detail=f"No employees found for country: {country}")
    return titles


@router.get("/country/{country}/job-title/{job_title}")
def country_job_title_stats(country: str, job_title: str, db: Session = Depends(get_db)):
    stats = svc.get_job_title_stats_in_country(db, country, job_title)
    if stats is None:
        raise HTTPException(status_code=404, detail=f"No data for '{job_title}' in {country}")
    return stats
