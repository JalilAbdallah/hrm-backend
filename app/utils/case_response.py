from typing import Dict, Any

def build_paginated_response(
    data: Dict[str, Any],
    filters: 'CaseFilters'
) -> Dict[str, Any]:
    
    total_count = data["total_count"]
    skip = filters.skip
    limit = filters.limit
    
    return {
        "cases": data["cases"],
        "pagination": {
            "total_count": total_count,
            "current_skip": skip,
            "current_limit": limit,
            "returned_count": data["returned_count"],
            "has_next": (skip + limit) < total_count,
            "has_prev": skip > 0
        },
        "filters_applied": {
            "violation_types": filters.violation_types, # Changed from status to violation_types
            "country": filters.country,
            "region": filters.region,
            "priority": filters.priority,
            "status": filters.status,
            "search": filters.search,
            "date_from": filters.date_from,
            "date_to": filters.date_to,
        }
    }