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
    producers = await db.producers.find().to_list(1000)
    producer_map = {str(p["_id"]): p.get("company_name", "") for p in producers}

    cursor = db.users.find().sort("created_at", -1)
    raw_users = await cursor.to_list(1000)

    users = []
    for u in raw_users:
        u["id"] = str(u["_id"])
        del u["_id"]
        if "password_hash" in u:
            del u["password_hash"]
        if u.get("producer_id"):
            u["producer_id"] = str(u["producer_id"])
            u["company_name"] = producer_map.get(u["producer_id"], "")
        else:
            u["company_name"] = ""
        users.append(u)
    return users
