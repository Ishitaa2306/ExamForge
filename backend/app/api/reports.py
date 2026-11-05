from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.core.dependencies import get_current_user
from app.database.connection import get_db
from app.database.models import Examination, ExaminationReport, User
from app.schemas.reports import ExaminationReportResponse

router = APIRouter()


@router.get("/examination/{examination_id}", response_model=ExaminationReportResponse)
def get_examination_report(
    examination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the AI-generated report for a completed examination."""
    exam = (
        db.query(Examination)
        .filter(Examination.id == examination_id, Examination.user_id == current_user.id)
        .first()
    )
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examination not found")

    report = (
        db.query(ExaminationReport)
        .filter(ExaminationReport.examination_id == examination_id)
        .first()
    )
    if not report:
        # If examination is complete but report not ready, try to generate it
        if exam.status.value == "COMPLETED":
            from app.services.report_service import ReportService
            try:
                report = ReportService.generate_report(db=db, examination=exam)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Report generation in progress. Please try again shortly."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not yet generated — complete the examination first"
            )
    return report


@router.get("/examination/{examination_id}/pdf")
def get_examination_report_pdf(
    examination_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a PDF version of the examination report."""
    exam = (
        db.query(Examination)
        .filter(Examination.id == examination_id, Examination.user_id == current_user.id)
        .first()
    )
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examination not found")

    report = (
        db.query(ExaminationReport)
        .filter(ExaminationReport.examination_id == examination_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    from app.services.report_service import ReportService
    pdf_bytes = ReportService.generate_pdf(db=db, report=report, examination=exam, user=current_user)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=examforge-report-{examination_id}.pdf"
        },
    )


@router.get("/", response_model=list[ExaminationReportResponse])
def list_reports(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all examination reports for the current user."""
    reports = (
        db.query(ExaminationReport)
        .filter(ExaminationReport.user_id == current_user.id)
        .order_by(ExaminationReport.generated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return reports
