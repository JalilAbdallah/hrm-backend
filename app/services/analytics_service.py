from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId
from config.database import get_database
from schemas.analytics_schema import (
    ViolationsAnalyticsResponse, GeodataResponse,
    DashboardResponse, TrendsResponse, RiskAssessmentResponse,
    ViolationCount, GeographicDataPoint,
    StatusCount, RiskLevelCount, YearlyTrendsData, ViolationTypeCount
)
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.db = get_database()
        self.cases_collection = self.db.cases
        self.reports_collection = self.db.incident_reports
        self.victims_collection = self.db.individuals
    
    def get_dashboard_analytics(self) -> DashboardResponse:
        try:
            total_cases = self.cases_collection.count_documents({})
            total_reports = self.reports_collection.count_documents({})
            total_victims = self.victims_collection.count_documents({})
            
            cases_by_status = self._get_status_distribution(self.cases_collection, "status")
            
            reports_by_status = self._get_status_distribution(self.reports_collection, "status")
            
            victims_by_risk = self._get_risk_distribution()
            
            recent_activity = self._get_recent_activity()
                        
            return DashboardResponse(
                total_cases=total_cases,
                total_reports=total_reports,
                total_victims=total_victims,
                cases_by_status=cases_by_status,
                reports_by_status=reports_by_status,
                victims_by_risk=victims_by_risk,
                recent_activity=recent_activity,
            )
            
        except Exception as e:
            logger.error(f"Error in dashboard analytics: {str(e)}")
            raise
    
    def get_trends_analytics(
        self, 
        year_from: int, 
        year_to: Optional[int] = None, 
        violation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if year_to is None:
            year_to = datetime.now().year
        
        if year_from > year_to:
            raise ValueError("year_from cannot be greater than year_to")
        
        all_violation_types = [
            "attack_on_medical",
            "attack_on_education", 
            "war_crimes",
            "civilian_targeting",
            "infrastructure_damage",
            "other"
        ]
        
        target_violation_types = violation_types if violation_types else all_violation_types
        
        invalid_types = [vt for vt in target_violation_types if vt not in all_violation_types]
        if invalid_types:
            raise ValueError(f"Invalid violation types: {invalid_types}")
        
        pipeline = [
            {
                "$match": {
                    "incident_details.date_occurred": {
                        "$gte": datetime(year_from, 1, 1),
                        "$lte": datetime(year_to, 12, 31, 23, 59, 59)
                    }
                }
            },
            {
                "$addFields": {
                    "year": {"$year": "$incident_details.date_occurred"}
                }
            },
            {
                "$unwind": "$incident_details.violation_types"
            },
            {
                "$match": {
                    "incident_details.violation_types": {"$in": target_violation_types}
                }
            },
            {
                "$group": {
                    "_id": {
                        "year": "$year",
                        "violation_type": "$incident_details.violation_types"
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {
                    "_id.year": 1,
                    "_id.violation_type": 1
                }
            }
        ]
        
        result = list(self.reports_collection.aggregate(pipeline))
        
        yearly_data = {}
        total_violations_all_years = 0
        
        for year in range(year_from, year_to + 1):
            yearly_data[year] = {
                "year": year,
                "violations": [],
                "total_violations": 0
            }
        
        for item in result:
            year = item["_id"]["year"]
            violation_type = item["_id"]["violation_type"]
            count = item["count"]
            
            if year in yearly_data:
                yearly_data[year]["violations"].append({
                    "violation_type": violation_type,
                    "count": count
                })
                yearly_data[year]["total_violations"] += count
                total_violations_all_years += count
        
        for year_data in yearly_data.values():
            existing_types = {v["violation_type"] for v in year_data["violations"]}
            
            for violation_type in target_violation_types:
                if violation_type not in existing_types:
                    year_data["violations"].append({
                        "violation_type": violation_type,
                        "count": 0
                    })
            
            year_data["violations"].sort(key=lambda x: x["violation_type"])
        
        data = list(yearly_data.values())
        
        return {
            "data": data,
            "years_analyzed": year_to - year_from + 1,
            "violation_types_included": target_violation_types,
            "total_violations_all_years": total_violations_all_years
        }

    def get_geodata_analytics(
        self,
        violation_type: Optional[str] = None,
        country: Optional[str] = None
    ) -> Dict[str, Any]:

        
        match_filters = {}
        
        if country:
            match_filters["incident_details.location.country"] = country
        
        if violation_type:
            match_filters["incident_details.violation_types"] = violation_type
        
        pipeline = [
            {"$match": match_filters},
            {
                "$group": {
                    "_id": {
                        "country": "$incident_details.location.country",
                        "city": "$incident_details.location.city",
                        "coordinates": "$incident_details.location.coordinates.coordinates"
                    },
                    "incident_count": {"$sum": 1},
                    "violation_types": {"$addToSet": {"$arrayElemAt": ["$incident_details.violation_types", 0]}}
                }
            },
            {
                "$match": {
                    "_id.coordinates": {"$exists": True, "$ne": None},
                    "_id.country": {"$exists": True, "$ne": None},
                    "_id.city": {"$exists": True, "$ne": None}
                }
            },
            {"$sort": {"incident_count": -1}}
        ]
        
        result = list(self.reports_collection.aggregate(pipeline))
        
        geodata_points = []
        
        for item in result:
            try:
                coordinates = item["_id"]["coordinates"]
                if coordinates and len(coordinates) >= 2:
                    geodata_point = GeographicDataPoint(
                        location={
                            "lat": coordinates[1],  # latitude
                            "lng": coordinates[0]   # longitude
                        },
                        region=item["_id"].get("city", "Unknown"),
                        country=item["_id"]["country"],
                        incident_count=item["incident_count"],
                        violation_types=item["violation_types"]
                    )
                    geodata_points.append(geodata_point)
            except (KeyError, IndexError, TypeError):
                continue
        
        return {
            "data": geodata_points,
            "total_locations": len(geodata_points)
        }
        
    def get_violations_analytics(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        violation_type: Optional[str] = None
    ) -> ViolationsAnalyticsResponse:
        try:
            match_filters = self._build_date_location_filters(date_from, date_to, country, city)
            
            if violation_type:
                match_filters["incident_details.violation_types"] = violation_type
            
            print(match_filters)
            reports_pipeline = [
                {"$match": match_filters},
                {"$unwind": "$incident_details.violation_types"},
                {"$group": {
                    "_id": "$incident_details.violation_types",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            
            print(f"Reports Pipeline: {reports_pipeline}")
            reports_result = list(self.reports_collection.aggregate(reports_pipeline))
            
            violation_counts = [
                ViolationCount(
                    violation_type=item["_id"],
                    count=item["count"]
                )
                for item in reports_result
            ]
            
            total_violations = sum(item.count for item in violation_counts)
            
            return ViolationsAnalyticsResponse(
                data=violation_counts,
                total_violations=total_violations,
                unique_types=len(violation_counts)
            )
            
        except Exception as e:
            logger.error(f"Error in violations analytics: {str(e)}")
            raise    
        
    
    def _build_date_location_filters(
        self, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        country: Optional[str] = None,
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        filters = {}
        
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                date_filter["$lte"] = date_to
            filters["incident_details.date_occurred"] = date_filter
        
        if country:
            filters["incident_details.location.country"] = country
        
        if city:
            filters["incident_details.location.city"] = city

        return filters
    
    def _combine_violation_counts(self, cases_result: List, reports_result: List) -> List[ViolationCount]:
        violation_map = {}
        
        for item in cases_result:
            violation_type = item["_id"]
            count = item["count"]
            violation_map[violation_type] = violation_map.get(violation_type, 0) + count
        
        for item in reports_result:
            violation_type = item["_id"]
            count = item["count"]
            violation_map[violation_type] = violation_map.get(violation_type, 0) + count
        

        result = [
            ViolationCount(violation_type=vtype, count=count)
            for vtype, count in violation_map.items()
        ]
        
        return sorted(result, key=lambda x: x.count, reverse=True)
    
    def _process_geodata_results(self, results: List) -> List[GeographicDataPoint]:
        """Process geographic aggregation results"""
        geodata = []
        
        for item in results:
            location_data = item["_id"]
            coordinates = location_data.get("coordinates", {})
            
            if coordinates and coordinates.get("coordinates"):
                coords = coordinates["coordinates"]
                geodata.append(GeographicDataPoint(
                    location={"lat": coords[1], "lng": coords[0]},
                    region=location_data.get("region", "Unknown"),
                    country=location_data.get("country", "Unknown"),
                    incident_count=item["incident_count"],
                    violation_types=item["violation_types"]
                ))
        
        return geodata
    
    def _get_date_grouping(self, period_type: str) -> Dict[str, Any]:
        """Get MongoDB date grouping expression based on period type"""
        if period_type == "monthly":
            return {
                "year": {"$year": "$date_occurred"},
                "month": {"$month": "$date_occurred"}
            }
        elif period_type == "weekly":
            return {
                "year": {"$year": "$date_occurred"},
                "week": {"$week": "$date_occurred"}
            }
        elif period_type == "daily":
            return {
                "year": {"$year": "$date_occurred"},
                "month": {"$month": "$date_occurred"},
                "day": {"$dayOfMonth": "$date_occurred"}
            }
        else:
            return {"year": {"$year": "$date_occurred"}}
    
    
    def _process_yearly_trends(
        self, 
        reports_result: List, 
        year_from: int, 
        year_to: int, 
        violation_types: List[str]
    ) -> List[YearlyTrendsData]:
        yearly_data = {}
        for year in range(year_from, year_to + 1):
            yearly_data[year] = {violation_type: 0 for violation_type in violation_types}
        
        
        for item in reports_result:
            year = item["_id"]["year"]
            violation_type = item["_id"]["violation_type"]
            count = item["count"]
            if year in yearly_data and violation_type in yearly_data[year]:
                yearly_data[year][violation_type] += count
        
        result = []
        for year in sorted(yearly_data.keys()):
            violations = [
                ViolationTypeCount(violation_type=vtype, count=count)
                for vtype, count in yearly_data[year].items()
            ]
            
            total_year_violations = sum(v.count for v in violations)
            
            result.append(YearlyTrendsData(
                year=year,
                violations=violations,
                total_violations=total_year_violations
            ))
        
        return result

    def _format_period(self, date_obj: Dict, period_type: str) -> str:
        if period_type == "monthly":
            return f"{date_obj['year']}-{date_obj['month']:02d}"
        elif period_type == "weekly":
            return f"{date_obj['year']}-W{date_obj['week']:02d}"
        elif period_type == "daily":
            return f"{date_obj['year']}-{date_obj['month']:02d}-{date_obj['day']:02d}"
        else:
            return str(date_obj['year'])
    
    
    def _get_status_distribution(self, collection, status_field: str) -> List[StatusCount]:
        """Get distribution of statuses from a collection"""
        pipeline = [
            {"$group": {"_id": f"${status_field}", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        result = list(collection.aggregate(pipeline))
        return [StatusCount(status=item["_id"], count=item["count"]) for item in result]
    
    def _get_risk_distribution(self) -> List[RiskLevelCount]:
        """Get risk level distribution from victims"""
        pipeline = [
            {"$group": {"_id": "$risk_assessment.level", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        result = list(self.victims_collection.aggregate(pipeline))
        return [RiskLevelCount(risk_level=item["_id"], count=item["count"]) for item in result]
    
    def _get_recent_activity(self) -> Dict[str, int]:
        """Get activity counts for last 30 days"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        recent_cases = self.cases_collection.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        recent_reports = self.reports_collection.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        return {
            "new_cases": recent_cases,
            "new_reports": recent_reports
        }
            
    def _get_violations_for_period(self, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """Get violation counts for a specific period"""
        return {}
    
    
    def _get_risk_level_distribution(self) -> Dict[str, int]:
        """Get distribution of risk levels"""
        return {}
    
    def _get_regions_by_risk_level(self, risk_level: str) -> List[str]:
        """Get regions filtered by risk level"""
        return []
    
    def _analyze_risk_factors(self) -> List[Dict[str, Any]]:
        """Analyze common risk factors"""
        return []
    
    def _generate_risk_recommendations(self, risk_dist: Dict, high_risk_regions: List[str]) -> List[str]:
        """Generate risk mitigation recommendations"""
        return []