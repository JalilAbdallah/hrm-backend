from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnalyticsFilters(BaseModel):
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    country: Optional[str] = Field(None, description="Filter by country")
    city: Optional[str] = Field(None, description="Filter by city")
    violation_type: Optional[str] = Field(None, description="Filter by violation type")

class TrendsFilters(BaseModel):
    year_from: int = Field(..., description="Start year (e.g., 2020)")
    year_to: Optional[int] = Field(None, description="End year (if null, uses current year)")
    violation_types: Optional[List[str]] = Field(None, description="List of violation types to include (if empty, includes all)")

class ReportGenerationRequest(BaseModel):
    format: str = Field(..., description="Report format: pdf or excel")
    title: Optional[str] = Field("Human Rights Analysis Report", description="Report title")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    country: Optional[str] = Field(None, description="Filter by country")
    region: Optional[str] = Field(None, description="Filter by region")
    violation_type: Optional[str] = Field(None, description="Filter by violation type")

class ViolationCount(BaseModel):
    violation_type: str
    count: int

class ViolationsAnalyticsResponse(BaseModel):
    data: List[ViolationCount]
    total_violations: int
    unique_types: int

class GeographicDataPoint(BaseModel):
    location: Dict[str, float]  # {"lat": float, "lng": float}
    region: str
    country: str
    incident_count: int
    violation_types: List[str]

class GeodataResponse(BaseModel):
    data: List[GeographicDataPoint]
    total_locations: int

class TimelineDataPoint(BaseModel):
    period: str  # "2023-01" for monthly, "2023-W01" for weekly
    cases: int
    reports: int
    total_incidents: int

class TimelineResponse(BaseModel):
    data: List[TimelineDataPoint]
    period_type: str  # "monthly", "weekly", "daily"
    total_periods: int

class StatusCount(BaseModel):
    status: str
    count: int

class RiskLevelCount(BaseModel):
    risk_level: str
    count: int

class DashboardResponse(BaseModel):
    total_cases: int
    total_reports: int
    total_victims: int
    cases_by_status: List[StatusCount]
    reports_by_status: List[StatusCount]
    victims_by_risk: List[RiskLevelCount]
    recent_activity: Dict[str, int]  # last 30 days

class ViolationTypeCount(BaseModel):
    violation_type: str
    count: int

class YearlyTrendsData(BaseModel):
    year: int
    violations: List[ViolationTypeCount]
    total_violations: int

class TrendsResponse(BaseModel):
    data: List[YearlyTrendsData]
    years_analyzed: int
    violation_types_included: List[str]
    total_violations_all_years: int


class RiskAssessmentResponse(BaseModel):
    risk_distribution: Dict[str, int]  # {"high": 15, "medium": 34, "low": 40}
    high_risk_regions: List[str]
    risk_factors: List[Dict[str, Any]]
    recommendations: List[str]

class ReportGenerationResponse(BaseModel):
    file_url: str
    file_name: str
    format: str
    generated_at: datetime
    expires_at: datetime