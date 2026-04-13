"""
Admin export endpoints.
EXP-04: Every export logged (who, when, which batch).
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_admin_user, get_db
from src.db.crud import get_batch_attendance, log_export_action
from src.export.pdf_exporter import export_attendance_pdf
from src.export.excel_exporter import export_attendance_excel
import time

router = APIRouter()


@router.get("/export/{batch_id}")
def export_attendance(
    batch_id: str,
    format: str = "pdf",
    admin=Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    EXP-01: Export batch attendance (≤10s for ≤200 students).
    EXP-04: Logs export action.
    """
    start = time.time()
    records, overrides, session_data = get_batch_attendance(db, batch_id)

    if not records:
        raise HTTPException(status_code=404, detail="No records found for this batch")

    if len(records) > 200:
        raise HTTPException(status_code=400, detail="Batch exceeds 200 student limit")

    if format == "pdf":
        content = export_attendance_pdf(session_data, records, overrides)
        media_type = "application/pdf"
        filename = f"attendance_{batch_id}.pdf"
    elif format == "excel":
        content = export_attendance_excel(session_data, records, overrides)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"attendance_{batch_id}.xlsx"
    else:
        raise HTTPException(status_code=400, detail="format must be 'pdf' or 'excel'")

    elapsed = time.time() - start
    log_export_action(db, admin.id, batch_id, format, len(records))

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
