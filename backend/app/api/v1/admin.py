from fastapi import APIRouter, Depends
from app.db.mongodb import get_database
from app.api.v1.auth import get_current_admin

router = APIRouter()

@router.get("/stats")
async def get_admin_stats(
    current_admin: dict = Depends(get_current_admin),
    db=Depends(get_database)
):
    producers = await db.producers.find({}, {"_id": 1, "status": 1}).to_list(5000)
    all_ids = [p["_id"] for p in producers]
    approved_ids = [p["_id"] for p in producers if p.get("status", "APPROVED") == "APPROVED"]

    def belongs_to(ids):
        # il collegamento alla cantina puo' essere salvato come ObjectId o come testo
        return {"producer_id": {"$in": ids + [str(i) for i in ids]}}

    total_products = await db.products.count_documents(belongs_to(all_ids))
    # come nel catalogo e nell'Osservatorio: vini pubblicati di cantine approvate
    published_products = await db.products.count_documents({"status": "PUBLISHED", **belongs_to(approved_ids)})
    # vini rimasti senza cantina (cantina eliminata o collegamento sbagliato): da sistemare
    orphan_products = await db.products.count_documents({"producer_id": {"$nin": all_ids + [str(i) for i in all_ids]}})
    total_inquiries = await db.inquiries.count_documents({})
    unread_inquiries = await db.inquiries.count_documents({"is_read": False})

    pending_producers = sum(1 for p in producers if p.get("status") == "PENDING_APPROVAL")
    deletion_requests = await db.producers.count_documents({"deletion_requested_at": {"$ne": None}})

    return {
        "pending_producers": pending_producers,
        "deletion_requests": deletion_requests,
        "total_producers": len(producers),
        "approved_producers": len(approved_ids),
        "total_products": total_products,
        "published_products": published_products,
        "orphan_products": orphan_products,
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
