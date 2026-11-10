import uuid
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session

from common.database import get_db
from models.classification_model import OCDEClassificationResponse, ODSClassificationResponse
from services.classification_service import MS2ClassificationWorker
from models import ClassificationRequest, ClassificationResultResponse

router = APIRouter(prefix="/classify", tags=["OCDE / ODS Classification"])

def get_worker():
    return MS2ClassificationWorker()

@router.post("/direct", response_model=ClassificationResultResponse)
async def classify_direct(payload: ClassificationRequest, db: Session = Depends(get_db), worker: MS2ClassificationWorker = Depends(get_worker)):
    """
    Ejecuta inferencia directa OCDE y ODS para un ítem, registrando bitácora en LLM_Classification_Log.
    """
    try:
        return await worker.execute_classification(
            item_id=payload.item_id,
            title=payload.title,
            abstract=payload.abstract,
            keywords=payload.keywords,
            db=db,
            temperature=payload.temperature,
            repetition_number=payload.repetition_number
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

