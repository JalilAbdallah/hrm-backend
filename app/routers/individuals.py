from fastapi import APIRouter, HTTPException, Depends
from typing import List
from schemas.individual_schema import VictimCreate, VictimOut, VictimOutSafe, VictimUpdateRisk
from schemas.waited_individual_schema import WaitedIndividualOut
from services.individuals_service import VictimService
from utils.conversion import convert_objectid_to_str

def get_victim_service() -> VictimService:
    return VictimService()

router = APIRouter()

@router.post("/")
def create_victim(
    victim: VictimCreate,
    service: VictimService = Depends(get_victim_service)
):
    victim_id = service.create_victim(victim.dict())
    return {"id": victim_id}

@router.get("/waited/", response_model=List[WaitedIndividualOut])
def get_waited_individuals(service: VictimService = Depends(get_victim_service)):
    return service.get_waited_individuals()

@router.get("/case/{case_id}")
def get_victims_by_case(
    case_id: str,
    service: VictimService = Depends(get_victim_service)
):
    victims = service.get_victims_by_case(case_id)
    return [convert_objectid_to_str(v) for v in victims]

@router.patch("/{victim_id}")
def update_risk_assessment(
    victim_id: str,
    risk: VictimUpdateRisk,
    service: VictimService = Depends(get_victim_service)
):
    success = service.update_risk_level(victim_id, risk.dict())
    if not success:
        raise HTTPException(status_code=404, detail="Victim not found or update failed")
    return {"message": "Risk level updated"}

@router.get("/{victim_id}")
def get_victim_by_id(
    victim_id: str,
    service: VictimService = Depends(get_victim_service)
):
    victim = service.get_victim_by_id(victim_id)
    if not victim:
        raise HTTPException(status_code=404, detail="Victim not found")

    victim = convert_objectid_to_str(victim)

    if victim.get("anonymous"):
        return VictimOutSafe(**victim)
    return VictimOut(**victim)
