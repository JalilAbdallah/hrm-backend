from pydantic import BaseModel, Field, validator
from typing import Optional
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
