from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from config.database import get_database
import logging

logger = logging.getLogger(__name__)

class CaseService:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.cases

    def get_cases(
        self,
        status: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        
        try:
            filter_query = self._build_filter_query(
                status, country, region, date_from, date_to
            )
            
            cursor = self.collection.find(filter_query).skip(skip).limit(limit)
            cases = [self._serialize_case(case) for case in cursor]
            
            total_count = self.collection.count_documents(filter_query)
            
            return {
                "cases": cases,
                "total_count": total_count,
                "returned_count": len(cases)
            }
        except Exception as e:
            logger.error(f"Error fetching cases: {str(e)}")
            raise

    def _build_filter_query(
        self,
        status: Optional[str],
        country: Optional[str],
        region: Optional[str],
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> Dict[str, Any]:
        
        filter_query = {}
        
        if status:
            filter_query["status"] = status
        
        if country:
            filter_query["location.country"] = {
                "$regex": country, "$options": "i"
            }
        
        if region:
            filter_query["location.region"] = {
                "$regex": region, "$options": "i"
            }
        
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                # Include entire day
                end_of_day = date_to.replace(hour=23, minute=59, second=59)
                date_filter["$lte"] = end_of_day
            filter_query["created_at"] = date_filter
        
        return filter_query

    def _serialize_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        if case is None:
            return None
        
        # Create a copy to avoid modifying the original
        serialized_case = dict(case)
    
        # Convert top-level ObjectId fields
        for field in ["_id", "created_by"]:
            if field in serialized_case and serialized_case[field]:
                if isinstance(serialized_case[field], ObjectId):
                    serialized_case[field] = str(serialized_case[field])
 
        # Convert ObjectIds in source_reports array
        if "source_reports" in serialized_case and serialized_case["source_reports"]:
            serialized_case["source_reports"] = [
               str(report_id) for report_id in serialized_case["source_reports"]
            ]
        
        # Convert ObjectIds in history array (if embedded)
        if "history" in serialized_case and serialized_case["history"]:
            for history_entry in serialized_case["history"]:
                if "updated_by" in history_entry and history_entry["updated_by"]:
                    if isinstance(history_entry["updated_by"], ObjectId):
                        history_entry["updated_by"] = str(history_entry["updated_by"])
                    elif isinstance(history_entry["updated_by"], dict) and "$oid" in history_entry["updated_by"]:
                        history_entry["updated_by"] = str(history_entry["updated_by"]["$oid"])
    
        return serialized_case
    
    # fetch a case by its ID
    def get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
      
        try:
            case = self.collection.find_one({"_id": ObjectId(case_id)})
            # Serialize the case before returning
            return self._serialize_case(case) if case else None
        except Exception as e:
            logger.error(f"Error fetching case by ID {case_id}: {str(e)}")
            raise
    
    def create_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Validate required fields
            required_fields = [
                "title", "description", "violation_types", "status",
                "priority", "location", "created_by"
            ]
            for field in required_fields:
                if field not in case_data or not case_data[field]:
                    raise ValueError(f"Missing required field: {field}")
            if "country" not in case_data["location"]:
                raise ValueError("Missing required field: location.country")

            # Convert IDs
            if isinstance(case_data["created_by"], str):
                case_data["created_by"] = ObjectId(case_data["created_by"])
            if "source_reports" in case_data:
                case_data["source_reports"] = [
                    ObjectId(r) if isinstance(r, str) else r
                    for r in case_data["source_reports"]
                ]

            # Set timestamps
            now = datetime.utcnow()
            case_data.setdefault("created_at", now)
            case_data.setdefault("updated_at", now)

            # Generate case_id if not provided
            if "case_id" not in case_data or not case_data["case_id"]:
                case_data["case_id"] = self.generate_case_id()

            # Insert the case
            result = self.collection.insert_one(case_data)
            inserted_case_id = str(result.inserted_id)

            # Create case_status_history document
            history_entry = self.build_case_history_entry(
                status=case_data["status"],
                updated_by=case_data["created_by"]
            )
            self.db.case_status_history.insert_one({
                "case_id": case_data["case_id"],
                "history": [history_entry]
            })

            # Return the created case
            return self.get_case_by_id(inserted_case_id)

        except Exception as e:
            logger.error(f"Error creating case: {str(e)}")
            raise


    
    # modifiy the case_status_history collection to store the history of case status changes
    def build_case_history_entry(self, status: str, updated_by: str) -> Dict[str, Any]:
        return {
            "status": status,
            "updated_at": datetime.utcnow(),
            "updated_by": ObjectId(updated_by) if isinstance(updated_by, str) else updated_by
        }
    
    def update_case(self, case_id: str, update_data: Dict[str, Any], updated_by: str) -> Optional[Dict[str, Any]]:
            try:
                # Validate case_id
                if not ObjectId.is_valid(case_id):
                    logger.error(f"Invalid case ID format: {case_id}")
                    raise ValueError("Invalid case ID format")

                # Validate update_data is not empty
                if not update_data:
                    logger.error("No fields provided for case update")
                    raise ValueError("No fields provided for update")

                # Fetch the existing case
                existing_case = self.collection.find_one({"_id": ObjectId(case_id)})
                if not existing_case:
                    logger.error(f"Case not found: {case_id}")
                    raise ValueError("Case not found")

                # Convert source_reports IDs to ObjectId if provided
                if "source_reports" in update_data:
                    try:
                        update_data["source_reports"] = [
                            ObjectId(r) if isinstance(r, str) and ObjectId.is_valid(r) else r
                            for r in update_data["source_reports"]
                        ]
                    except Exception as e:
                        logger.error(f"Invalid source_reports ID: {str(e)}")
                        raise ValueError(f"Invalid source_reports ID: {str(e)}")

                # Convert updated_by to ObjectId if it’s a valid ObjectId string
                try:
                    update_data["updated_by"] = ObjectId(updated_by) if ObjectId.is_valid(updated_by) else updated_by
                except Exception as e:
                    logger.error(f"Invalid updated_by ID: {str(e)}")
                    raise ValueError(f"Invalid updated_by ID: {str(e)}")

                # Set updated_at timestamp
                update_data["updated_at"] = datetime.utcnow()

                # Update the case with partial data
                result = self.collection.update_one(
                    {"_id": ObjectId(case_id)},
                    {"$set": update_data}
                )

                # If status changed, update case_status_history
                if "status" in update_data and update_data["status"] != existing_case.get("status"):
                    history_entry = self.build_case_history_entry(update_data["status"], updated_by)
                    self.db.case_status_history.update_one(
                        {"case_id": existing_case.get('case_id')},  # Use _id instead of case_id
                        {"$push": {"history": history_entry}},
                        upsert=True
                    )
                    
                # Return the updated case
                return self.get_case_by_id(case_id)

            except ValueError as e:
                logger.error(f"Error updating case {case_id}: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Error updating case {case_id}: {str(e)}")
                raise
        


