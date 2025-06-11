from fastapi import APIRouter, HTTPException, Depends
from typing import List
from schemas.individual_schema import VictimCreate, VictimOut, VictimOutSafe, VictimUpdateRisk
from schemas.waited_individual_schema import WaitedIndividualOut, UpdateWaitedVictimsRequest
from services.analytics_service import analytics_service as AnalyticsService
from utils.conversion import convert_objectid_to_str
from middleware.auth import require_admin,require_institution,access_both 


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


router = APIRouter()


@router.get("/", response_model=List[WaitedIndividualOut])
def get_waited_individuals(
    current_user: dict =Depends(require_admin),
    service: VictimService = Depends(get_victim_service)):
    return service.get_waited_individuals()

