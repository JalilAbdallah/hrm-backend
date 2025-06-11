from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class ReportFilters(BaseModel):
    status: Optional[str] = Field(None)
    country: Optional[str] = Field(None)
    city: Optional[str] = Field(None)
    date_from: Optional[str] = Field(None)
    date_to: Optional[str] = Field(None)
        
    @validator('date_from', 'date_to')
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v

class Coordinates(BaseModel):
    type: str = Field(default="Point")
    coordinates: List[float] = Field(...)

class Location(BaseModel):
    country: str = Field(...)
    city: str = Field(...)
    coordinates: Coordinates = Field(...)

class IncidentDetails(BaseModel):
    title: str = Field(...)
    description: str = Field(...)
    date_occurred: datetime = Field(...)
    location: Location = Field(...)
    violation_types: List[str] = Field(...)
    estimated_victims: int = Field(0, ge=0)

class Victim(BaseModel):
    name: str = Field(...)
    occupation: str = Field(...)
    gender: str = Field(...)
    age: int = Field(..., ge=0, le=150)

class Evidence(BaseModel):
    type: str = Field(...)
    url: str = Field(...)
    description: Optional[str] = Field(None)

class CreateIncidentReport(BaseModel):
    institution_id: str = Field(...)
    anonymous: bool = Field(False)
    incident_details: IncidentDetails = Field(...)
    victims: List[Victim] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    
class UpdateReportStatus(BaseModel):
    status: str = Field(...)

class IncidentReportResponse(BaseModel):
    id: str = Field(...)
    report_id: str = Field(...)
    status: str = Field(...)
    created_at: datetime = Field(...)
    message: str = Field(...)

class UpdateReportResponse(BaseModel):
    report_id: str = Field(...)
    status: str = Field(...)
    updated_at: datetime = Field(...)
    message: str = Field(...)