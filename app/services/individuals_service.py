from typing import Optional, List, Dict, Any
from bson import ObjectId, errors
from config.database import get_database
from datetime import datetime
import logging
from utils.conversion import convert_objectid_to_str
from schemas.waited_individual_schema import WaitedIndividualOut

logger = logging.getLogger(__name__)


class VictimService:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.individuals

    def create_victim(self, victim_data: Dict[str, Any]) -> str:
        try:
            now = datetime.utcnow()
            victim_data["created_at"] = now
            victim_data["updated_at"] = now
            result = self.collection.insert_one(victim_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating victim: {e}")
            raise

    def get_victim_by_id(self, victim_id: str) -> Optional[Dict[str, Any]]:
        try:
            if not ObjectId.is_valid(victim_id):
                return None
            victim = self.collection.find_one({"_id": ObjectId(victim_id)})
            if victim:
                return convert_objectid_to_str(victim)
            return None
        except Exception as e:
            logger.error(f"Error retrieving victim: {e}")
            raise

    def update_risk_level(self, victim_id: str, risk_data: dict) -> bool:
        try:
            update_query = {
                "risk_assessment.level": risk_data.get("level"),
                "risk_assessment.threats": risk_data.get("threats"),
                "risk_assessment.protection_needed": risk_data.get("protection_needed")
            }

            update_query = {k: v for k, v in update_query.items() if v is not None}

            result = self.collection.update_one(
                {"_id": ObjectId(victim_id)},
                {"$set": update_query}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating risk: {e}")
            return False

    def get_victims_by_case(self, case_id: str) -> List[Dict[str, Any]]:
        try:
            if not ObjectId.is_valid(case_id):
                return []
            victims = self.collection.find({
                "cases_involved": ObjectId(case_id)
            })
            return [convert_objectid_to_str(v) for v in victims]
        except Exception as e:
            logger.error(f"Error fetching victims by case: {e}")
            raise

    def get_waited_individuals(self) -> list[WaitedIndividualOut]:
        try:
            waited_collection = self.db.waited_individuals
            individuals = waited_collection.find()

            results = []
            for ind in individuals:
                ind["_id"] = str(ind["_id"])
                ind["case_id"] = str(ind["case_id"])
                ind["id"] = ind.pop("_id")
                results.append(WaitedIndividualOut(**ind))

            return results

        except Exception as e:
            logger.error(f"Error fetching waited individuals: {e}")
            raise

    def update_waited_victims(self, waited_id: str, victims: List[dict]) -> bool:
        try:
            obj_id = ObjectId(waited_id)
        except errors.InvalidId:
            logger.error(f"Invalid ObjectId: {waited_id}")
            return False

        result = self.db.waited_individuals.update_one(
            {"_id": obj_id},
            {"$set": {"victims": victims}}
        )

        logger.info(f"Matched: {result.matched_count}, Modified: {result.modified_count}")
        return result.matched_count > 0
