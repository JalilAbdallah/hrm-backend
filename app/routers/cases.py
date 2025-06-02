from fastapi import APIRouter, HTTPException, status as HTTPStatus, Depends
from datetime import datetime
from services.case_service import CaseService
from schemas.case_schema import CaseFilters, CaseUpdateRequest
from utils.case_response import build_paginated_response

router = APIRouter()

def get_case_service() -> CaseService:
    return CaseService()

@router.get("/")
async def list_cases(
    filters: CaseFilters = Depends(),
    case_service: CaseService = Depends(get_case_service)
):
    try:
        date_from = None
        date_to = None
        
        if filters.date_from:
            date_from = datetime.strptime(filters.date_from, "%Y-%m-%d")
        
        if filters.date_to:
            date_to = datetime.strptime(filters.date_to, "%Y-%m-%d")
        
        data = case_service.get_cases(
            status=filters.status,
            country=filters.country,
            region=filters.region,
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
            detail="Internal server error while fetching cases" + str(e)
        )


@router.get("/{case_id}")
async def get_case(case_id: str, case_service: CaseService = Depends(get_case_service)):
    try:
        case = case_service.get_case_by_id(case_id)
        if not case:
            raise HTTPException(
                status_code=HTTPStatus.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )
        return case
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching case"
        )
    
@router.post("/create")
async def create_case(case_data: dict, case_service: CaseService = Depends(get_case_service)):
    try:
        new_case = case_service.create_case(case_data)
        return {
            "message": "Case created successfully",
            "case": new_case
        }
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while creating case {str(e)}"
        )
    
@router.patch("/update/{case_id}")
async def update_case(
    case_id: str, 
    request: CaseUpdateRequest,
    case_service: CaseService = Depends(get_case_service)
):
    try:
        updated_case = case_service.update_case(case_id, request.case_data, request.updated_by)
        if not updated_case:
            raise HTTPException(
                status_code=HTTPStatus.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )
        return {
            "message": "Case updated successfully",
            "case": updated_case
        }
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while updating case {str(e)}"
        )    