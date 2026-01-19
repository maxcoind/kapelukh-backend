from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks

from app.auth import get_current_user
from app.crud import survey as survey_crud
from app.crud.survey import SortField, SortOrder
from app.database import getDbSession
from app.models.survey import Survey
from app.schemas.survey import SurveyCreate, SurveyRead, SurveyUpdate
from app.websocket.routes import get_connection_manager
from app.websocket.integration import ModelEventHelper
from app.websocket.plugins.survey_plugin import SurveyPlugin

router = APIRouter()


async def trigger_survey_event(
    survey: Survey, event_type: Literal["created", "updated", "deleted"], session
):
    """Trigger survey event via EventProcessor."""
    connection_manager = get_connection_manager()

    plugin = SurveyPlugin()
    await ModelEventHelper.trigger_event(
        db=session,
        connection_manager=connection_manager,
        topic="survey",
        event_type=event_type,
        instance=survey,
        to_dict_func=plugin.to_dict,
    )


@router.post("/", response_model=SurveyRead, status_code=status.HTTP_201_CREATED)
async def create_survey(
    *,
    session=Depends(getDbSession),
    survey_in: SurveyCreate,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> Survey:
    survey = await survey_crud.create(session=session, survey_create=survey_in)
    background_tasks.add_task(trigger_survey_event, survey, "created", session)
    return survey


@router.get("/{survey_id}", response_model=SurveyRead)
async def read_survey(
    *,
    session=Depends(getDbSession),
    survey_id: int,
    current_user: str = Depends(get_current_user),
) -> Survey:
    survey = await survey_crud.get(session=session, survey_id=survey_id)
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found"
        )
    return survey


@router.get("/by-user/{user_id}", response_model=SurveyRead)
async def read_survey_by_user_id(
    *,
    session=Depends(getDbSession),
    user_id: int,
    current_user: str = Depends(get_current_user),
) -> Survey:
    survey = await survey_crud.get_by_user_id(session=session, user_id=user_id)
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found for this user",
        )
    return survey


@router.get("/", response_model=List[SurveyRead])
async def read_surveys(
    *,
    session=Depends(getDbSession),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None),
    sort_by: Optional[SortField] = Query(
        None, description="Field to sort by (user_id, created_at, birth_date)"
    ),
    sort_order: Optional[SortOrder] = Query(
        SortOrder.asc, description="Sort order (asc, desc)"
    ),
    current_user: str = Depends(get_current_user),
) -> List[Survey]:
    surveys = await survey_crud.get_multi(
        session=session,
        skip=skip,
        limit=limit,
        user_id=user_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return surveys


@router.put("/{survey_id}", response_model=SurveyRead)
async def update_survey(
    *,
    session=Depends(getDbSession),
    survey_id: int,
    survey_in: SurveyUpdate,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> Survey:
    db_survey = await survey_crud.get(session=session, survey_id=survey_id)
    if not db_survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found"
        )
    survey = await survey_crud.update(
        session=session, db_obj=db_survey, obj_in=survey_in
    )
    background_tasks.add_task(trigger_survey_event, survey, "updated", session)
    return survey


@router.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_survey(
    *,
    session=Depends(getDbSession),
    survey_id: int,
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks,
) -> None:
    survey = await survey_crud.remove(session=session, survey_id=survey_id)
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found"
        )
    background_tasks.add_task(trigger_survey_event, survey, "deleted", session)
