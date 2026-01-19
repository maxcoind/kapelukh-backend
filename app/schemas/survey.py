from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SortField(str, Enum):
    user_id = "user_id"
    created_at = "created_at"
    birth_date = "birth_date"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class SurveyBase(BaseModel):
    user_id: int
    full_name: Dict[str, str] = {}
    super_powers: List[str] = []
    birth_date: str
    traits_to_improve: List[str] = []
    to_buy: List[str] = []
    to_sell: List[str] = []
    service: Optional[str] = None
    material_goal: Optional[str] = None
    social_goal: Optional[str] = None
    spiritual_goal: Optional[str] = None


class SurveyCreate(SurveyBase):
    user_id: int = Field(description="Telegram ID пользователя")
    birth_date: str = Field(min_length=1)


class SurveyUpdate(BaseModel):
    full_name: Optional[Dict[str, str]] = None
    super_powers: Optional[List[str]] = None
    birth_date: Optional[str] = None
    traits_to_improve: Optional[List[str]] = None
    to_buy: Optional[List[str]] = None
    to_sell: Optional[List[str]] = None
    service: Optional[str] = None
    material_goal: Optional[str] = None
    social_goal: Optional[str] = None
    spiritual_goal: Optional[str] = None


class SurveyRead(SurveyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserSurvey(BaseModel):
    full_name: Dict[str, str] = {}
    super_powers: List[str] = []
    birth_date: str = ""
    traits_to_improve: List[str] = []
    to_buy: List[str] = []
    to_sell: List[str] = []
    service: Optional[str] = None
    material_goal: Optional[str] = None
    social_goal: Optional[str] = None
    spiritual_goal: Optional[str] = None


class ValidationResult(BaseModel):
    is_valid: bool
    data: UserSurvey
    suggestions: Optional[str] = None
