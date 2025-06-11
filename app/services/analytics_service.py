from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId
from config.database import get_database
from schemas.analytics_schema import (
    ViolationsAnalyticsResponse, GeodataResponse, TimelineResponse,
    DashboardResponse, TrendsResponse, RiskAssessmentResponse,
    ViolationCount, GeographicDataPoint, TimelineDataPoint,
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
            # Get basic counts
            total_cases = self.cases_collection.count_documents({})
            total_reports = self.reports_collection.count_documents({})
            total_victims = self.victims_collection.count_documents({})
            
            # Get cases by status
            cases_by_status = self._get_status_distribution(self.cases_collection, "status")
            
            # Get reports by status  
            reports_by_status = self._get_status_distribution(self.reports_collection, "status")
            
            # Get victims by risk level
            victims_by_risk = self._get_risk_distribution()
            
            # Get recent activity (last 30 days)
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
        """
        Get trends analytics showing violation counts by year and type
        
        Args:
            year_from: Starting year for analysis
            year_to: Ending year (if None, uses current year)
            violation_types: List of violation types to filter by (if None, includes all)
        
        Returns:
            Dictionary matching TrendsResponse schema structure
        """
        # Set default end year to current year if not provided
        if year_to is None:
            year_to = datetime.now().year
        
        # Validate year range
        if year_from > year_to:
            raise ValueError("year_from cannot be greater than year_to")
        
        # Define all possible violation types
        all_violation_types = [
            "attack_on_medical",
            "attack_on_education", 
            "war_crimes",
            "civilian_targeting",
            "infrastructure_damage",
            "other"
        ]
        
        # Use provided violation types or default to all
        target_violation_types = violation_types if violation_types else all_violation_types
        
        # Validate violation types
        invalid_types = [vt for vt in target_violation_types if vt not in all_violation_types]
        if invalid_types:
            raise ValueError(f"Invalid violation types: {invalid_types}")
        
        # Build MongoDB aggregation pipeline
        pipeline = [
            # Match documents within the year range
            {
                "$match": {
                    "incident_details.date_occurred": {
                        "$gte": datetime(year_from, 1, 1),
                        "$lte": datetime(year_to, 12, 31, 23, 59, 59)
                    }
                }
            },
            # Add year field for grouping
            {
                "$addFields": {
                    "year": {"$year": "$incident_details.date_occurred"}
                }
            },
            # Unwind violation_types array to process each violation separately
            {
                "$unwind": "$incident_details.violation_types"
            },
            # Filter by target violation types
            {
                "$match": {
                    "incident_details.violation_types": {"$in": target_violation_types}
                }
            },
            # Group by year and violation type
            {
                "$group": {
                    "_id": {
                        "year": "$year",
                        "violation_type": "$incident_details.violation_types"
                    },
                    "count": {"$sum": 1}
                }
            },
            # Sort by year and violation type
            {
                "$sort": {
                    "_id.year": 1,
                    "_id.violation_type": 1
                }
            }
        ]
        
        # Execute aggregation
        result = list(self.reports_collection.aggregate(pipeline))
        
        # Process results into the required format
        yearly_data = {}
        total_violations_all_years = 0
        
        # Initialize structure for all years in range
        for year in range(year_from, year_to + 1):
            yearly_data[year] = {
                "year": year,
                "violations": [],
                "total_violations": 0
            }
        
        # Process aggregation results
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
        
        # Ensure all violation types are represented for each year (with 0 counts if needed)
        for year_data in yearly_data.values():
            existing_types = {v["violation_type"] for v in year_data["violations"]}
            
            for violation_type in target_violation_types:
                if violation_type not in existing_types:
                    year_data["violations"].append({
                        "violation_type": violation_type,
                        "count": 0
                    })
            
            # Sort violations by type for consistency
            year_data["violations"].sort(key=lambda x: x["violation_type"])
        
        # Convert to list format required by schema
        data = list(yearly_data.values())
        
        return {
            "data": data,
            "years_analyzed": year_to - year_from + 1,
            "violation_types_included": target_violation_types,
            "total_violations_all_years": total_violations_all_years
        }

    
    # Helper methods
    def _build_date_location_filters(
        self, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        country: Optional[str] = None,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build MongoDB filter query for date and location"""
        filters = {}
        
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                date_filter["$lte"] = date_to
            filters["date_occurred"] = date_filter
        
        if country:
            filters["location.country"] = country
        
        if region:
            filters["location.region"] = region
            
        return filters
    
    def _combine_violation_counts(self, cases_result: List, reports_result: List) -> List[ViolationCount]:
        """Combine violation counts from cases and reports"""
        violation_map = {}
        
        # Process cases results
        for item in cases_result:
            violation_type = item["_id"]
            count = item["count"]
            violation_map[violation_type] = violation_map.get(violation_type, 0) + count
        
        # Process reports results
        for item in reports_result:
            violation_type = item["_id"]
            count = item["count"]
            violation_map[violation_type] = violation_map.get(violation_type, 0) + count
        
        # Convert to list and sort
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
                    location={"lat": coords[1], "lng": coords[0]},  # MongoDB stores [lng, lat]
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
    
    def _combine_timeline_data(self, cases_result: List, reports_result: List, period_type: str) -> List[TimelineDataPoint]:
        """Combine timeline data from cases and reports"""
        timeline_map = {}
        
        # Process cases
        for item in cases_result:
            period = self._format_period(item["_id"], period_type)
            timeline_map[period] = timeline_map.get(period, {"cases": 0, "reports": 0})
            timeline_map[period]["cases"] = item["cases"]
        
        # Process reports
        for item in reports_result:
            period = self._format_period(item["_id"], period_type)
            timeline_map[period] = timeline_map.get(period, {"cases": 0, "reports": 0})
            timeline_map[period]["reports"] = item["reports"]
        
        # Convert to list
        result = []
        for period, data in sorted(timeline_map.items()):
            result.append(TimelineDataPoint(
                period=period,
                cases=data["cases"],
                reports=data["reports"],
                total_incidents=data["cases"] + data["reports"]
            ))
        
        return result
    
    def _process_yearly_trends(
        self, 
        reports_result: List, 
        year_from: int, 
        year_to: int, 
        violation_types: List[str]
    ) -> List[YearlyTrendsData]:
        """Process and combine yearly trends data from cases and reports"""
        
        # Initialize data structure for all years and violation types
        yearly_data = {}
        for year in range(year_from, year_to + 1):
            yearly_data[year] = {violation_type: 0 for violation_type in violation_types}
        
        
        # Process reports results
        for item in reports_result:
            year = item["_id"]["year"]
            violation_type = item["_id"]["violation_type"]
            count = item["count"]
            if year in yearly_data and violation_type in yearly_data[year]:
                yearly_data[year][violation_type] += count
        
        # Convert to response format
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
        """Format date object to period string"""
        if period_type == "monthly":
            return f"{date_obj['year']}-{date_obj['month']:02d}"
        elif period_type == "weekly":
            return f"{date_obj['year']}-W{date_obj['week']:02d}"
        elif period_type == "daily":
            return f"{date_obj['year']}-{date_obj['month']:02d}-{date_obj['day']:02d}"
        else:
            return str(date_obj['year'])
    
    # Additional helper methods would be implemented here
    # (Status distribution, risk analysis, etc.)
    
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
            
    # Additional helper methods for trends and risk assessment...
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