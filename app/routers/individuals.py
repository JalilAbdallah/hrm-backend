from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Union
from schemas.individual_schema import VictimCreate, VictimOut, VictimOutSafe, VictimUpdateRisk
from services.individuals_service import VictimService
from utils.conversion import convert_objectid_to_str
from bson import ObjectId



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


@router.get("/{victim_id}")
def get_victim_by_id(
        victim_id: str,
        service: VictimService = Depends()
):
    victim = service.get_victim_by_id(victim_id)
    if not victim:
        raise HTTPException(status_code=404, detail="Victim not found")

    victim = convert_objectid_to_str(victim)

    if victim.get("anonymous"):
        return VictimOutSafe(**victim)
    return VictimOut(**victim)


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


@router.get("/case/{case_id}")
def get_victims_by_case(case_id: str, service: VictimService = Depends(get_victim_service)):
    victims = service.get_victims_by_case(case_id)
    return [convert_objectid_to_str(v) for v in victims]

