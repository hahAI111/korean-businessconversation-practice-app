"""
发音评分 API
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user_id
from app.schemas.schemas import PronunciationRequest, PronunciationResult
from app.services.speech_service import assess_pronunciation

router = APIRouter(prefix="/api/pronunciation", tags=["pronunciation"])


@router.post("", response_model=PronunciationResult)
async def score_pronunciation(
    body: PronunciationRequest,
    user_id: int = Depends(get_current_user_id),
):
    """对用户韩语发音评分。"""
    result = await assess_pronunciation(
        audio_base64=body.audio_base64,
        reference_text=body.reference_text,
        language=body.language,
    )
    if result["pronunciation_score"] == 0 and not result["words"]:
        raise HTTPException(status_code=400, detail="无法评估发音，请重试")
    return result
