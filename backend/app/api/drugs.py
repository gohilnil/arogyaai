"""
app/api/drugs.py — Drug Interaction Checker API
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.security import get_current_user
from app.services.drug_checker import drug_checker_service

logger = logging.getLogger("arogyaai.drugs")
router = APIRouter(prefix="/api/drugs", tags=["Drugs"])


class DrugCheckRequest(BaseModel):
    medications: List[str]


class DrugSuggestRequest(BaseModel):
    query: str


@router.post("/check-interactions")
async def check_drug_interactions(
    req: DrugCheckRequest,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """Check interactions between a list of medications."""
    if not req.medications or len(req.medications) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least 2 medications to check interactions.",
        )
    if len(req.medications) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 medications can be checked at once.",
        )

    user_profile = None
    # Could fetch from DB here if user is logged in
    result = await drug_checker_service.check_interactions(
        medications=req.medications,
        user_profile=user_profile,
    )
    return result


@router.post("/suggest")
async def suggest_medications(req: DrugSuggestRequest):
    """Autocomplete medication names."""
    suggestions = drug_checker_service.get_medication_suggestions(req.query)
    return {"suggestions": suggestions}
