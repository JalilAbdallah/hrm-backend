from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from config.database import get_database
import logging

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.incident_reports
    
    def get_reports(
        self,
        status: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        try:
            filter_query = self._build_filter_query(
                status, country, city, date_from, date_to
            )
            
            cursor = self.collection.find(filter_query).skip(skip).limit(limit)
            reports = [self._serialize_report(report) for report in cursor]
            
            total_count = self.collection.count_documents(filter_query)
            
            return {
                "reports": reports,
                "total_count": total_count,
                "returned_count": len(reports)
            }
        except Exception as e:
            logger.error(f"Error fetching reports: {str(e)}")
            raise
    
    def _build_filter_query(
        self,
        status: Optional[str],
        country: Optional[str], 
        city: Optional[str],
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> Dict[str, Any]:
        filter_query = {}
        
        if status:
            filter_query["status"] = status
        
        if country:
            filter_query["incident_details.location.country"] = {
                "$regex": country, "$options": "i"
            }
        
        if city:
            filter_query["incident_details.location.city"] = {
                "$regex": city, "$options": "i"
            }
        
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                # Include entire day
                end_of_day = date_to.replace(hour=23, minute=59, second=59)
                date_filter["$lte"] = end_of_day
            filter_query["incident_details.date_occurred"] = date_filter
        
        return filter_query
    
    def _serialize_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        if report is None:
            return None
        
        for field in ["_id", "institution_id", "assigned_admin", "linked_case_id"]:
            if field in report and report[field]:
                report[field] = str(report[field])
        
        return report
