import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import AppRole
from app.services import import_service

router = APIRouter(prefix="/content/import", tags=["content"])


@router.post("", dependencies=[Depends(require_role(AppRole.admin))])
async def upload_curriculum_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Import courses, units, lessons, and questions from a CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported currently.")

    content = await file.read()
    csv_file = io.StringIO(content.decode("utf-8"))

    try:
        results = await import_service.import_curriculum_csv(db, csv_file)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
