"""
Vocabulary book API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.models.models import VocabBook
from app.schemas.schemas import VocabAddRequest, VocabResponse

router = APIRouter(prefix="/api/vocab", tags=["vocab"])


@router.get("", response_model=list[VocabResponse])
async def list_vocab(
    mastered: bool | None = None,
    tag: str | None = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query = select(VocabBook).where(VocabBook.user_id == user_id)
    if mastered is not None:
        query = query.where(VocabBook.mastered == mastered)
    result = await db.execute(query.order_by(VocabBook.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=VocabResponse)
async def add_vocab(
    body: VocabAddRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    vocab = VocabBook(
        user_id=user_id,
        word_ko=body.word_ko,
        word_romanized=body.word_romanized,
        meaning_zh=body.meaning_zh,
        example_sentence=body.example_sentence,
        tags=body.tags,
    )
    db.add(vocab)
    await db.commit()
    await db.refresh(vocab)
    return vocab


@router.patch("/{vocab_id}/master")
async def toggle_mastered(
    vocab_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VocabBook).where(VocabBook.id == vocab_id, VocabBook.user_id == user_id)
    )
    vocab = result.scalar_one_or_none()
    if not vocab:
        raise HTTPException(status_code=404, detail="Not found")
    vocab.mastered = not vocab.mastered
    vocab.review_count += 1
    await db.commit()
    return {"mastered": vocab.mastered}


@router.put("/{vocab_id}", response_model=VocabResponse)
async def update_vocab(
    vocab_id: int,
    body: VocabAddRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VocabBook).where(VocabBook.id == vocab_id, VocabBook.user_id == user_id)
    )
    vocab = result.scalar_one_or_none()
    if not vocab:
        raise HTTPException(status_code=404, detail="Not found")
    vocab.word_ko = body.word_ko
    vocab.word_romanized = body.word_romanized
    vocab.meaning_zh = body.meaning_zh
    vocab.example_sentence = body.example_sentence
    vocab.tags = body.tags
    await db.commit()
    await db.refresh(vocab)
    return vocab


@router.delete("/{vocab_id}")
async def delete_vocab(
    vocab_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VocabBook).where(VocabBook.id == vocab_id, VocabBook.user_id == user_id)
    )
    vocab = result.scalar_one_or_none()
    if not vocab:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(vocab)
    await db.commit()
    return {"deleted": True}
