from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from sqlmodel import and_, asc, desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.survey import Survey
from app.schemas.survey import SurveyCreate, SurveyUpdate, ValidationResult


class SortField(str, Enum):
    user_id = "user_id"
    created_at = "created_at"
    birth_date = "birth_date"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


async def create(*, session: AsyncSession, survey_create: SurveyCreate) -> Survey:
    db_obj = Survey.model_validate(survey_create)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def get(*, session: AsyncSession, survey_id: int) -> Optional[Survey]:
    return await session.get(Survey, survey_id)


async def get_by_user_id(*, session: AsyncSession, user_id: int) -> Optional[Survey]:
    statement = select(Survey).where(Survey.user_id == user_id)
    result = await session.exec(statement)
    return result.first()


async def get_multi(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    sort_by: Optional[SortField] = None,
    sort_order: Optional[SortOrder] = None,
) -> List[Survey]:
    statement = select(Survey)
    conditions = []

    if user_id is not None:
        conditions.append(Survey.user_id == user_id)

    if conditions:
        statement = statement.where(and_(*conditions))

    if sort_by:
        sort_column = getattr(Survey, sort_by.value)
        if sort_order == SortOrder.desc:
            statement = statement.order_by(desc(sort_column))
        else:
            statement = statement.order_by(asc(sort_column))

    statement = statement.offset(skip).limit(limit)
    result = await session.exec(statement)
    return list(result.all())


async def update(
    *, session: AsyncSession, db_obj: Survey, obj_in: SurveyUpdate
) -> Survey:
    obj_data = obj_in.model_dump(exclude_unset=True)
    for field, value in obj_data.items():
        setattr(db_obj, field, value)
    db_obj.updated_at = datetime.now(timezone.utc)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def remove(*, session: AsyncSession, survey_id: int) -> Optional[Survey]:
    obj = await session.get(Survey, survey_id)
    if obj:
        await session.delete(obj)
        await session.commit()
    return obj


async def save_user_survey(
    *, session: AsyncSession, user_id: int, validation_result: ValidationResult
) -> Survey:
    survey_data = SurveyCreate(
        user_id=user_id,
        full_name=validation_result.data.full_name,
        super_powers=validation_result.data.super_powers,
        birth_date=validation_result.data.birth_date,
        traits_to_improve=validation_result.data.traits_to_improve,
        to_buy=validation_result.data.to_buy,
        to_sell=validation_result.data.to_sell,
        service=validation_result.data.service,
        material_goal=validation_result.data.material_goal,
        social_goal=validation_result.data.social_goal,
        spiritual_goal=validation_result.data.spiritual_goal,
    )
    return await create(session=session, survey_create=survey_data)
