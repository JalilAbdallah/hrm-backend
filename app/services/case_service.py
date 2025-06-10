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
        self.archived_collection = self.db.archived_cases

    def _process_object_id_array(self, data, field_name: str) -> List[ObjectId]:
        """
        Process array field that can contain ObjectIds (victims, source_reports)
        Accepts single item or array, converts strings to ObjectIds
        """
        if not isinstance(data, list):
            # If single item, convert to list
            data = [data]
        
        processed_items = []
        for item in data:
            if isinstance(item, str) and ObjectId.is_valid(item):
                processed_items.append(ObjectId(item))
            elif isinstance(item, ObjectId):
                processed_items.append(item)
            else:
                raise ValueError(f"Invalid ObjectId format in {field_name}: {item}")
        
        return processed_items

    def _validate_case_id(self, case_id: str) -> None:
        """Validate ObjectId format and raise ValueError if invalid"""
        if not ObjectId.is_valid(case_id):
            logger.error(f"Invalid case ID format: {case_id}")
            raise ValueError("Invalid case ID format")

    def _query_cases_with_pagination(self, collection, filter_query: Dict[str, Any], skip: int, limit: int) -> Dict[str, Any]:
        """Query cases from a collection with pagination and return formatted result"""
        print(f"Querying cases with filter: {filter_query}, skip: {skip}, limit: {limit}")
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        cases = [self._serialize_case(case) for case in cursor]
        
        total_count = collection.count_documents(filter_query)
        
        return {
            "cases": cases,
            "total_count": total_count,
            "returned_count": len(cases)
        }

    def _find_case_by_id(self, collection, case_id: str) -> Optional[Dict[str, Any]]:
        """Find a case by ID from the specified collection"""
        case = collection.find_one({"_id": ObjectId(case_id)})
        return self._serialize_case(case) if case else None

    def _move_case_between_collections(self, source_collection, target_collection, case_id: str, operation_name: str) -> bool:
        """Move a case from source collection to target collection"""
        self._validate_case_id(case_id)
        
        # Find the case in source collection
        case_to_move = source_collection.find_one({"_id": ObjectId(case_id)})
        
        if not case_to_move:
            logger.warning(f"No case found to {operation_name} with ID: {case_id}")
            return False

        # Insert the case into target collection
        target_collection.insert_one(case_to_move)
        
        # Remove the case from source collection
        result = source_collection.delete_one({"_id": ObjectId(case_id)})

        if result.deleted_count == 0:
            # If deletion failed, remove from target collection to maintain consistency
            target_collection.delete_one({"_id": ObjectId(case_id)})
            logger.error(f"Failed to delete case from source collection during {operation_name}: {case_id}")
            return False
        
        logger.info(f"Successfully {operation_name}d case {case_id}")
        return True

    def _build_filter_query(
        self,
        violation_types: Optional[str], # Changed from violation_type to violation_types
        country: Optional[str],
        region: Optional[str],
        status: Optional[str],
        priority: Optional[str],
        search: Optional[str],
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> Dict[str, Any]:
        
        filter_query = {}
        
        if violation_types: # Changed from violation_type to violation_types
            # Assuming violation_types is a comma-separated string of types
            # Convert to a list and use $all to match documents containing all specified types
            types_list = [vt.strip() for vt in violation_types.split(',') if vt.strip()]
            if types_list:
                filter_query["violation_types"] = {"$all": types_list}
        
        if country:
            filter_query["location.country"] = {
                "$regex": country, "$options": "i"
            }
        
        if region:
            filter_query["location.region"] = {
                "$regex": region, "$options": "i"
            }
        if status:
            filter_query["status"] = status
        
        if priority:
            filter_query["priority"] = priority
        
        if search:
            filter_query["title"] = {"$regex": search, "$options": "i"}

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

        def convert_extended_json(obj: Any) -> Any:
            if isinstance(obj, dict):
                if "$oid" in obj:
                    return str(obj["$oid"])  # Convert {"$oid": "..."} to string
                elif "$date" in obj:
                    return obj["$date"]  # Already ISO format, use as is
                return {k: convert_extended_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_extended_json(item) for item in obj]
            elif isinstance(obj, ObjectId):
                return str(obj)
            return obj

        # Create a copy to avoid modifying the original
        serialized_case = convert_extended_json(dict(case))
        return serialized_case
    
    def get_cases(
        self,
        violation_types: Optional[str] = None, # Changed from violation_type to violation_types
        country: Optional[str] = None,
        region: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        
        try:
            filter_query = self._build_filter_query(
                violation_types, country, region, status, priority, search, date_from, date_to
            )
            
            return self._query_cases_with_pagination(self.collection, filter_query, skip, limit)
        except Exception as e:
            logger.error(f"Error fetching cases: {str(e)}")
            raise

    # fetch a case by its ID
    def get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        try:
            return self._find_case_by_id(self.collection, case_id)
        except Exception as e:
            logger.error(f"Error fetching case by ID {case_id}: {str(e)}")
            raise
    
    def create_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Validate required fields
            required_fields = [
                "title", "description", "violation_types",
                "priority", "location"
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
            if "victims" in case_data:
                case_data["victims"] = [
                    ObjectId(v) if isinstance(v, str) else v
                    for v in case_data["victims"]
                ]
            

            # Set timestamps
            now = datetime.utcnow()
            case_data.setdefault("created_at", now)
            case_data.setdefault("updated_at", now)

            # Generate case_id if not provided
            number_of_cases = self.collection.count_documents({})
            number_of_archived_cases = self.archived_collection.count_documents({})
            year = now.year
            new_case_id= f"HRM-{year}-{4000+number_of_cases + number_of_archived_cases + 1}"
            case_data["case_id"] = new_case_id

            case_data["status"] = "new"  # Default status for new cases
            # Insert the case
            result = self.collection.insert_one(case_data)
            inserted_case_id = str(result.inserted_id)

            # Create case_status_history document
            history_entry = self.build_case_history_entry(
                status="new",
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
    
    def get_case_status_history(self, case_id: str) -> List[Dict[str, Any]]:
        try:
        
            # Fetch the status history for the case
            history = self.db.case_status_history.find_one({"case_id": case_id})
            if not history:
                logger.warning(f"No status history found for case ID: {case_id}")
                return []

            # Convert ObjectId to string for serialization
            for entry in history.get("history", []):
                if "updated_by" in entry and isinstance(entry["updated_by"], ObjectId):
                    entry["updated_by"] = str(entry["updated_by"])

            return history.get("history", [])
        except Exception as e:
            logger.error(f"Error fetching case status history for {case_id}: {str(e)}")
            raise

    def update_case(self, case_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            try:
                # Validate case_id
                self._validate_case_id(case_id)

                # Validate update_data is not empty
                if not update_data:
                    logger.error("No fields provided for case update")
                    raise ValueError("No fields provided for update")


                # --- NEW: updated_by requirement for status change ---
                if "status" in update_data:
                    if not update_data["updated_by"]:
                        raise ValueError("updated_by is required when updating status.")

                # Fetch the existing case
                existing_case = self.collection.find_one({"_id": ObjectId(case_id)})
                if not existing_case:
                    logger.error(f"Case not found: {case_id}")
                    raise ValueError("Case not found")

                fields_to_set = {}                # Process 'victims' if present in update_data
                if "victims" in update_data:
                    try:
                        fields_to_set["victims"] = self._process_object_id_array(update_data["victims"], "victims")
                    except ValueError as ve:
                        logger.error(f"Error processing victim IDs: {str(ve)}")
                        raise
                    except Exception as e:
                        logger.error(f"Invalid victim ID in victims list: {str(e)}")
                        raise ValueError(f"Invalid victim ID in victims list: {str(e)}")
                
                # Process 'source_reports' if present in update_data
                if "source_reports" in update_data:
                    try:
                        fields_to_set["source_reports"] = self._process_object_id_array(update_data["source_reports"], "source_reports")
                    except ValueError as ve:
                        logger.error(f"Error processing source report IDs: {str(ve)}")
                        raise
                    except Exception as e:
                        logger.error(f"Invalid source report ID in source_reports list: {str(e)}")
                        raise ValueError(f"Invalid source report ID in source_reports list: {str(e)}")
                
                # Process 'status' if present in update_data
                if "status" in update_data:
                    fields_to_set["status"] = update_data["status"]
                    
                # Set updated_at timestamp
                fields_to_set["updated_at"] = datetime.utcnow()                # Initialize updated_by variable
                updated_by = None
                
                # Convert and add updated_by (the function parameter) to the document update, if provided
                if update_data.get("updated_by"):
                    updated_by = update_data["updated_by"]
                    try:
                        if ObjectId.is_valid(updated_by):
                            fields_to_set["updated_by"] = ObjectId(updated_by)
                        else:
                            # If updated_by is provided but not a valid ObjectId string
                            raise ValueError(f"Invalid ObjectId format for updated_by parameter: {updated_by}")
                    except ValueError as ve: # Catch our ValueError or ObjectId's
                        logger.error(f"Error processing updated_by parameter: {str(ve)}")
                        raise
                    except Exception as e: # Catch other BSON errors
                        logger.error(f"Invalid updated_by ID for document update: {str(e)}")
                        raise ValueError(f"Invalid updated_by ID for document update: {str(e)}")
                
                # Perform the update only if there's something to set
                if not fields_to_set:
                    logger.info(f"No fields to update for case {case_id} after processing. Skipping database update.")
                    return self.get_case_by_id(case_id) # Return current state
                
                result = self.collection.update_one(
                    {"_id": ObjectId(case_id)},
                    {"$set": fields_to_set}
                )

                # If status changed, update case_status_history
                if "status" in update_data and update_data["status"] != existing_case.get("status"):
                    # updated_by (param) is guaranteed to be present if status is in update_data due to earlier check
                    history_entry = self.build_case_history_entry(update_data["status"], updated_by)
                    self.db.case_status_history.update_one(
                        {"case_id": existing_case.get('case_id')},  # Use case_id
                        {"$push": {"history": history_entry}},
                        upsert=True
                    )
                    
                # Return the updated case
                if result.modified_count == 0:
                    logger.warning(f"No changes were made to case {case_id}")
                    return self.get_case_by_id(case_id)
                
                logger.info(f"Successfully updated case {case_id}")
                return self.get_case_by_id(case_id)

            except ValueError as e:
                logger.error(f"Error updating case {case_id}: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Error updating case {case_id}: {str(e)}")
                raise
        
    def archive_case(self, case_id: str) -> bool:
        try:
            return self._move_case_between_collections(
                self.collection, 
                self.archived_collection, 
                case_id, 
                "archive"
            )
        except Exception as e:
            logger.error(f"Error archiving case {case_id}: {str(e)}")
            raise
    
    def get_archived_cases(
        self,
        violation_types: Optional[str] = None, # Changed from violation_type to violation_types
        country: Optional[str] = None,
        region: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get archived cases with the same filtering options as regular cases"""
        try:
            filter_query = self._build_filter_query(
                violation_types, country, region, date_from, date_to # Changed from violation_type to violation_types
            )
            
            return self._query_cases_with_pagination(self.archived_collection, filter_query, skip, limit)
        except Exception as e:
            logger.error(f"Error fetching archived cases: {str(e)}")
            raise
    
    def get_archived_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Fetch an archived case by its ID"""
        try:
            return self._find_case_by_id(self.archived_collection, case_id)
        except Exception as e:
            logger.error(f"Error fetching archived case by ID {case_id}: {str(e)}")
            raise
    
    def restore_case(self, case_id: str) -> bool:
        """Restore a case from archived_cases back to cases collection"""
        try:
            return self._move_case_between_collections(
                self.archived_collection, 
                self.collection, 
                case_id, 
                "restore"
            )
        except Exception as e:
            logger.error(f"Error restoring case {case_id}: {str(e)}")
            raise

