from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime

class CaseFilters(BaseModel):
    violation_types: Optional[str] = Field(None, description="Filter by violation types")
    status: Optional[str] = Field(None, description="Filter by case status")
    country: Optional[str] = Field(None, description="Filter by country")
    region: Optional[str] = Field(None, description="Filter by region")
    priority: Optional[str] = Field(None, description="Filter by case priority")
    search: Optional[str] = Field(None, description="Search term for case title or description")
    date_from: Optional[str] = Field(None, description="Filter from date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Filter to date (YYYY-MM-DD)")
    skip: int = Field(0, ge=0, description="Number of cases to skip")
    limit: int = Field(100, ge=1, le=500, description="Maximum cases to return")

    @validator('date_from', 'date_to')
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = {"open", "closed", "under_investigation"}
        if v is not None and v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v
    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = {"low", "medium", "high"}
        if v is not None and v not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")
        return v

class CaseUpdateRequest(BaseModel):
    case_data: Dict[str, Any] = Field(..., description="The case data to update")
