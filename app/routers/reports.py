from fastapi import APIRouter, HTTPException, status as HTTPStatus, Depends
from datetime import datetime
from services.report_service import ReportService
from schemas.report_schema import ReportFilters, CreateIncidentReport, IncidentReportResponse, UpdateReportResponse, UpdateReportStatus
from utils.response_utils import build_paginated_response

router = APIRouter()

def get_report_service() -> ReportService:
    return ReportService()

@router.get("/")

async def list_reports(
    filters: ReportFilters = Depends(),
    report_service: ReportService = Depends(get_report_service)
):
    try:
        date_from = None
        date_to = None
        
        if filters.date_from:
            date_from = datetime.strptime(filters.date_from, "%Y-%m-%d")
        
        if filters.date_to:
            date_to = datetime.strptime(filters.date_to, "%Y-%m-%d")
        
        data = report_service.get_reports(
            status=filters.status,
            country=filters.country,
            city=filters.city,
            date_from=date_from,
            date_to=date_to,
            skip=filters.skip,
            limit=filters.limit
        )
        
        return build_paginated_response(data, filters)
        
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching reports"
        )
        
@router.post("/", status_code=HTTPStatus.HTTP_201_CREATED)
async def create_incident_report(
    report_data: CreateIncidentReport,
    report_service: ReportService = Depends(get_report_service)
):
    try:
        result = report_service.create_report(report_data)
        
        return IncidentReportResponse(
            id=result["id"],
            report_id=result["report_id"],
            status=result["status"],
            created_at=result["created_at"],
            message="Incident report created successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating report"
        )
        
@router.patch("/{report_id}", response_model=UpdateReportResponse, status_code=HTTPStatus.HTTP_200_OK)
async def update_report_status(
    report_id: str,
    status_data: UpdateReportStatus,
    report_service: ReportService = Depends(get_report_service)
):
    try:
        result = report_service.update_report_status(report_id, status_data)
        
        return UpdateReportResponse(
            report_id=result["report_id"],
            status=result["status"],
            updated_at=result["updated_at"],
            message="Report status updated successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating report status"
        )