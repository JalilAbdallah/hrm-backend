from fastapi import APIRouter, HTTPException, status as HTTPStatus, Depends, Query
from datetime import datetime
from typing import Optional
from services.analytics_service import AnalyticsService
from schemas.analytics_schema import (
    AnalyticsFilters, ReportGenerationRequest,
    ViolationsAnalyticsResponse, GeodataResponse, TimelineResponse,
    DashboardResponse, TrendsResponse, RiskAssessmentResponse,
    ReportGenerationResponse, TrendsFilters
)

router = APIRouter()

def get_analytics_service():
    return AnalyticsService()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard_analytics(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    try:
        data = analytics_service.get_dashboard_analytics()
        return data
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching dashboard analytics"
        )
        
@router.get("/trends")
async def get_trends_analytics(
    filters: TrendsFilters = Depends(),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):

    try:
        
        data = analytics_service.get_trends_analytics(
            year_from=filters.year_from,
            year_to=filters.year_to,
            violation_types=filters.violation_types
        )
        
        return data
        
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
@router.get("/violations", response_model=ViolationsAnalyticsResponse)
async def get_violations_analytics(
    filters: AnalyticsFilters = Depends(),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    try:
        date_from = None
        date_to = None
        
        if filters.date_from:
            date_from = datetime.strptime(filters.date_from, "%Y-%m-%d")
        
        if filters.date_to:
            date_to = datetime.strptime(filters.date_to, "%Y-%m-%d")
        
        data = analytics_service.get_violations_analytics(
            date_from=date_from,
            date_to=date_to,
            country=filters.country,
            city=filters.city,
            violation_type=filters.violation_type
        )
        
        return data
        
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching violations analytics"
        )


@router.get("/geodata", response_model=GeodataResponse)
async def get_geodata_analytics(
    violation_type: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    try:
        data = analytics_service.get_geodata_analytics(
            violation_type=violation_type,
            country=country
        )
        return data
        
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching geodata analytics"
        )