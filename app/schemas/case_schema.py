from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime

class CaseFilters(BaseModel):
    violation_types: Optional[str] = Field(None, description="Filter by violation types")
    country: Optional[str] = Field(None, description="Filter by country")
    region: Optional[str] = Field(None, description="Filter by region")
    date_from: Optional[str] = Field(None, description="Filter from date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Filter to date (YYYY-MM-DD)")
    skip: int = Field(0, ge=0, description="Number of cases to skip")
    limit: int = Field(100, ge=1, le=500, description="Maximum cases to return")

    # @validator('violation_type')
    # def validate_violation_type(cls, v):
    #     if v is not None and not isinstance(v, str):
    #         raise ValueError("Violation type must be a string")
    #     return v

    @validator('date_from', 'date_to')
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v

class CaseUpdateRequest(BaseModel):
    case_data: Dict[str, Any] = Field(..., description="The case data to update")
    updated_by: str = Field(..., description="ID of the user making the update")