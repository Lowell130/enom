from fastapi import APIRouter, Depends, HTTPException
from app.db.mongodb import get_database
from app.api.v1.auth import get_current_admin
from bson import ObjectId

router = APIRouter()

@router.get("/stats")
async def get_admin_stats(
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    total_producers = await db.producers.count_documents({})
    approved_producers = await db.producers.count_documents({"status": "APPROVED"})
    total_products = await db.products.count_documents({})
    published_products = await db.products.count_documents({"status": "PUBLISHED"})
    total_inquiries = await db.inquiries.count_documents({})
    unread_inquiries = await db.inquiries.count_documents({"is_read": False})
    
    return {
        "total_producers": total_producers,
        "approved_producers": approved_producers,
        "total_products": total_products,
        "published_products": published_products,
        "total_inquiries": total_inquiries,
        "unread_inquiries": unread_inquiries
    }

@router.get("/users")
async def get_all_users(
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    cursor = db.users.find().sort("created_at", -1)
    users = []
    async for u in cursor:
        u["id"] = str(u["_id"])
        del u["_id"]
        if "password_hash" in u:
            del u["password_hash"]
        if u.get("producer_id"):
            u["producer_id"] = str(u["producer_id"])
            prod = await db.producers.find_one({"_id": ObjectId(u["producer_id"])})
            if prod:
                u["company_name"] = prod.get("company_name", "")
        users.append(u)
    return users
