from fastapi import APIRouter, HTTPException, status as HTTPStatus, Depends
from datetime import datetime
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


