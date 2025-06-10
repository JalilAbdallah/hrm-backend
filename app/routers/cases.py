from fastapi import APIRouter, HTTPException, status as HTTPStatus, Depends
from datetime import datetime
from typing import Optional, Tuple, Any, Dict
from services.case_service import CaseService
from schemas.case_schema import CaseFilters, CaseUpdateRequest
from utils.case_response import build_paginated_response

router = APIRouter()

def get_case_service() -> CaseService:
    return CaseService()

# Helper functions to reduce code duplication
def parse_date_filters(filters: CaseFilters) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Converts string dates (YYYY-MM-DD) to datetime objects. Returns (date_from, date_to)."""
    date_from = None
    date_to = None
    
    if filters.date_from:
        date_from = datetime.strptime(filters.date_from, "%Y-%m-%d")
    
    if filters.date_to:
        date_to = datetime.strptime(filters.date_to, "%Y-%m-%d")
    
    return date_from, date_to

def handle_not_found(resource: Any, resource_name: str) -> None:
    """Raises 404 HTTPException if resource is None/False. Used for consistent not found errors."""
    if not resource:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} not found"
        )

def build_success_response(message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Creates standardized success response: {"message": str, ...data}."""
    response = {"message": message}
    if data:
        response.update(data)
    return response

def get_cases_with_filters(case_service: CaseService, filters: CaseFilters, get_method_name: str):
    """Common filtering logic for cases/archived cases. Parses dates, applies filters, returns paginated result."""
    date_from, date_to = parse_date_filters(filters)
    
    get_method = getattr(case_service, get_method_name)
    data = get_method(
        violation_types=filters.violation_types, # Correctly pass violation_types
        country=filters.country,
        region=filters.region,
        date_from=date_from,
        date_to=date_to,
        status=filters.status,
        priority=filters.priority,
        search=filters.search,
        skip=filters.skip,
        limit=filters.limit
    )
    
    return build_paginated_response(data, filters)

@router.get("/")
async def list_cases(
    filters: CaseFilters = Depends(),
    case_service: CaseService = Depends(get_case_service)
):
    """
    Get paginated list of active cases with optional filters.
    Query params: status, country, region, date_from, date_to, skip, limit
    Returns: {cases: [], total_count: int, returned_count: int, ...pagination}
    Errors: 400 (invalid dates), 500 (server error)
    """
    try:
        return get_cases_with_filters(case_service, filters, "get_cases")
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while fetching cases: {str(e)}"
        )


@router.get("/{case_id}")
async def get_case(case_id: str, case_service: CaseService = Depends(get_case_service)):
    """
    Get single case by ID.
    Path param: case_id (ObjectId string)
    Returns: Case object with all details
    Errors: 400 (invalid ID), 404 (not found), 500 (server error)
    """
    try:
        case = case_service.get_case_by_id(case_id)
        handle_not_found(case, "Case")
        return case
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while fetching case: {str(e)}"
        )
    
@router.post("/")
async def create_case(case_data: dict, case_service: CaseService = Depends(get_case_service)):
    """
    Create new case with required fields validation.
    Body: case data dict (title, description, violation_types, status, priority, location, created_by)
    Returns: {"message": "success", "case": created_case}
    Errors: 400 (missing fields), 500 (server error)
    """
    try:
        new_case = case_service.create_case(case_data)
        return build_success_response("Case created successfully", {"case": new_case})
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while creating case: {str(e)}"
        )
    
@router.patch("/{case_id}")
async def update_case(
    case_id: str, 
    request: CaseUpdateRequest,
    case_service: CaseService = Depends(get_case_service)
):
    """
    Update existing case with partial data. Auto-updates history if status changes.
    Path param: case_id, Body: {case_data: dict, updated_by: string}
    Returns: {"message": "success", "case": updated_case}
    Errors: 400 (invalid ID/data), 404 (not found), 500 (server error)
    """
    try:
        updated_case = case_service.update_case(case_id, request.case_data)
        handle_not_found(updated_case, "Case")
        return build_success_response("Case updated successfully", {"case": updated_case})
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while updating case: {str(e)}"
        )    
    

@router.post("/archive/{case_id}/restore")
async def restore_case(
    case_id: str, case_service: CaseService = Depends(get_case_service)
):
    """
    Restore archived case back to active cases collection.
    Path param: case_id (ObjectId string)
    Returns: {"message": "Case restored successfully", "case_id": "..."}
    Errors: 400 (invalid ID), 404 (archived case not found), 500 (server error)
    """
    try:
        result = case_service.restore_case(case_id)
        handle_not_found(result, "Archived case")
        return build_success_response("Case restored successfully", {"case_id": case_id})
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while restoring case: {str(e)}"
        )

@router.delete('/{case_id}')
async def delete_case(case_id: str, case_service: CaseService = Depends(get_case_service)):
    """
    Archive case (soft delete) - moves from cases to archived_cases collection.
    Path param: case_id (ObjectId string)
    Returns: {"message": "Case archived successfully"}
    Errors: 400 (invalid ID), 404 (not found), 500 (server error)
    """
    try:
        result = case_service.archive_case(case_id)
        handle_not_found(result, "Case")
        return build_success_response("Case archived successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while archiving case: {str(e)}"
        )

@router.get("/archive/")
async def list_archived_cases(
    filters: CaseFilters = Depends(),
    case_service: CaseService = Depends(get_case_service)
):
    """
    Get paginated list of archived cases with optional filters.
    Query params: status, country, region, date_from, date_to, skip, limit
    Returns: {cases: [], total_count: int, returned_count: int, ...pagination}
    Errors: 400 (invalid dates), 500 (server error)
    """
    try:
        return get_cases_with_filters(case_service, filters, "get_archived_cases")
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while fetching archived cases: {str(e)}"
        )


@router.get("/archive/{case_id}")
async def get_archived_case(
    case_id: str, case_service: CaseService = Depends(get_case_service)
):
    """
    Get single archived case by ID.
    Path param: case_id (ObjectId string)
    Returns: Archived case object with all details
    Errors: 400 (invalid ID), 404 (not found), 500 (server error)
    """
    try:
        archived_case = case_service.get_archived_case_by_id(case_id)
        handle_not_found(archived_case, "Archived case")
        return archived_case
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while fetching archived case: {str(e)}"
        )


@router.get("/history/{case_id}")
async def get_case_history(
    case_id: str, case_service: CaseService = Depends(get_case_service)
):
    """
    Get status change history for a case.
    Path param: case_id (ObjectId string)
    Returns: History array with status changes, timestamps, and users
    Errors: 400 (invalid ID), 404 (history not found), 500 (server error)
    """
    try:
        history = case_service.get_case_status_history(case_id)
        handle_not_found(history, "Case history")
        return history
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while fetching case history: {str(e)}"
        )
