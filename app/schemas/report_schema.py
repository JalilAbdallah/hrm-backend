from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class ReportFilters(BaseModel):
    status: Optional[str] = Field(None, description="Filter by report status")
    country: Optional[str] = Field(None, description="Filter by country")
    city: Optional[str] = Field(None, description="Filter by city")
    date_from: Optional[str] = Field(None, description="Filter from date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Filter to date (YYYY-MM-DD)")
    skip: int = Field(0, ge=0, description="Number of reports to skip")
    limit: int = Field(100, ge=1, le=500, description="Maximum reports to return")
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["new", "open", "closed"]
            if v not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v
    
    @validator('date_from', 'date_to')
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v

class Coordinates(BaseModel):
    type: str = Field(default="Point", description="GeoJSON type")
    coordinates: List[float] = Field(..., description="[longitude, latitude]")

class Location(BaseModel):
    country: str = Field(..., description="Country where incident occurred")
    city: str = Field(..., description="City where incident occurred")
    coordinates: Coordinates = Field(..., description="Geographic coordinates")

class IncidentDetails(BaseModel):
    title: str = Field(..., description="Brief title of the incident")
    description: str = Field(..., description="Detailed description of the incident")
    date_occurred: datetime = Field(..., description="When the incident occurred")
    location: Location = Field(..., description="Location details")
    violation_types: List[str] = Field(..., description="Types of violations")
    estimated_victims: int = Field(0, ge=0, description="Estimated number of victims")

class Victim(BaseModel):
    name: str = Field(..., description="Name of the victim")
    occupation: str = Field(..., description="Occupation of the victim")
    gender: str = Field(..., description="Gender of the victim")
    age: int = Field(..., ge=0, le=150, description="Age of the victim")

class Evidence(BaseModel):
    type: str = Field(..., description="Type of evidence (photo, video, document, etc.)")
    filename: str = Field(..., description="Original filename")
    url: str = Field(..., description="URL path to the evidence file")
    description: Optional[str] = Field(None, description="Description of the evidence")

class CreateIncidentReport(BaseModel):
    report_id: str = Field(..., description="Unique report identifier")
    institution_id: str = Field(..., description="ID of the reporting institution")
    anonymous: bool = Field(False, description="Whether the report is anonymous")
    incident_details: IncidentDetails = Field(..., description="Details of the incident")
    victims: List[Victim] = Field(default_factory=list, description="List of victims")
    evidence: List[Evidence] = Field(default_factory=list, description="List of evidence")
    

class IncidentReportResponse(BaseModel):
    id: str = Field(..., description="Database ID of the created report")
    report_id: str = Field(..., description="Report identifier")
    status: str = Field(..., description="Current status of the report")
    created_at: datetime = Field(..., description="Creation timestamp")
    message: str = Field(..., description="Success message")