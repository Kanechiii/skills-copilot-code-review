"""
Announcement management endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements (today's date is between start and expiration dates)"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Find announcements that are active today
    query = {
        "$expr": {
            "$and": [
                {"$lte": ["$start_date", today]},
                {"$gte": ["$expiration_date", today]}
            ]
        }
    }
    
    announcements = []
    for ann in announcements_collection.find(query).sort("created_at", -1):
        ann["_id"] = str(ann["_id"])
        announcements.append(ann)
    
    return announcements


@router.get("/all")
def get_all_announcements(username: str) -> List[Dict[str, Any]]:
    """Get all announcements (for admin panel) - only accessible by signed-in users"""
    # Verify user exists
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    announcements = []
    for ann in announcements_collection.find().sort("created_at", -1):
        ann["_id"] = str(ann["_id"])
        announcements.append(ann)
    
    return announcements


@router.post("")
def create_announcement(
    username: str,
    title: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new announcement - only accessible by signed-in users"""
    # Verify user exists
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Use start_date if provided, otherwise use today
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    
    # Validate dates
    if start_date > expiration_date:
        raise HTTPException(
            status_code=400,
            detail="Start date must be before or equal to expiration date"
        )
    
    announcement = {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "created_by": username,
        "created_at": datetime.now().isoformat()
    }
    
    result = announcements_collection.insert_one(announcement)
    announcement["_id"] = str(result.inserted_id)
    
    return announcement


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    username: str,
    title: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Update an announcement - only accessible by signed-in users"""
    # Verify user exists
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Verify announcement exists
    try:
        ann_id = ObjectId(announcement_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    announcement = announcements_collection.find_one({"_id": ann_id})
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Use start_date if provided, otherwise keep existing
    if start_date is None:
        start_date = announcement.get("start_date")
    
    # Validate dates
    if start_date > expiration_date:
        raise HTTPException(
            status_code=400,
            detail="Start date must be before or equal to expiration date"
        )
    
    update_data = {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "updated_at": datetime.now().isoformat()
    }
    
    announcements_collection.update_one({"_id": ann_id}, {"$set": update_data})
    
    # Fetch and return updated announcement
    updated = announcements_collection.find_one({"_id": ann_id})
    updated["_id"] = str(updated["_id"])
    
    return updated


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, username: str) -> Dict[str, str]:
    """Delete an announcement - only accessible by signed-in users"""
    # Verify user exists
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Verify announcement exists
    try:
        ann_id = ObjectId(announcement_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    result = announcements_collection.delete_one({"_id": ann_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    return {"message": "Announcement deleted successfully"}
