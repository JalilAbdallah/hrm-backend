from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
from datetime import datetime


class Demographics(BaseModel):
    gender: Optional[str]
    age: Optional[int]
    occupation: Optional[str]
    ethnicity: Optional[str]


class ContactInfo(BaseModel):
    email: Optional[EmailStr]
    phone: Optional[str]
    secure_messaging: Optional[str]


class RiskAssessment(BaseModel):
    level: Literal["low", "medium", "high"]
    threats: List[str]
    protection_needed: bool


class SupportService(BaseModel):
    type: str
    provider: str
    status: Literal["active", "inactive"]


class CreationContext(BaseModel):
    source_report: str
    source_case: str
    created_by_admin: str


class VictimCreate(BaseModel):
    type: Literal["victim", "witness"]
    name: str
    anonymous: bool
    demographics: Demographics
    contact_info: Optional[ContactInfo]
    risk_assessment: RiskAssessment
    support_services: List[SupportService]
    creation_context: CreationContext


class VictimOutSafe(BaseModel):
    _id: str
    type: Literal["victim", "witness"]
    name: str
    anonymous: bool
    demographics: Demographics
    risk_assessment: RiskAssessment
    support_services: List[SupportService]
    creation_context: CreationContext
    created_at: datetime
    updated_at: datetime


class VictimOut(VictimOutSafe):
    contact_info: Optional[ContactInfo]


class VictimUpdateRisk(BaseModel):
    level: Optional[str]
    threats: Optional[List[str]]
    protection_needed: Optional[bool]
