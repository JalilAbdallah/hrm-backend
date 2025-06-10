from datetime import datetime
from bson import ObjectId


def convert_objectid_to_str(victim: dict):
    _id = victim.get("_id")
    print("id: " + str(_id))
    if _id:
        victim["id"] = str(_id)
    else:
        victim["id"] = None

    victim.pop("_id", None)

    def parse_datetime(date_str: str):
        if date_str and isinstance(date_str, str):
            if "(" in date_str:
                date_str = date_str.split(" (")[0]
            try:
                return datetime.strptime(date_str.strip(), "%a %b %d %Y %H:%M:%S GMT%z")
            except Exception:
                return date_str
        return None

    if isinstance(victim.get("created_at"), str):
        victim["created_at"] = parse_datetime(victim["created_at"])
    if isinstance(victim.get("updated_at"), str):
        victim["updated_at"] = parse_datetime(victim["updated_at"])

    context = victim.get("creation_context", {})
    for key in ["source_report", "source_case", "created_by_admin"]:
        if key in context and isinstance(context[key], ObjectId):
            context[key] = str(context[key])

    if "created_by" in victim and isinstance(victim["created_by"], ObjectId):
        victim["created_by"] = str(victim["created_by"])

    if "cases_involved" in victim and isinstance(victim["cases_involved"], list):
        victim["cases_involved"] = [
            str(oid) if isinstance(oid, ObjectId) else oid
            for oid in victim["cases_involved"]
        ]

    return victim
