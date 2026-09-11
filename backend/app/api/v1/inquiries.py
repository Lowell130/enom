from fastapi import APIRouter, Depends, HTTPException, status
from app.db.mongodb import get_database
from app.schemas.inquiry import InquiryCreate, InquiryResponse
from app.api.v1.auth import get_current_user
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter()

@router.post("", response_model=InquiryResponse)
async def submit_inquiry(inquiry_in: InquiryCreate, db=Depends(get_database)):
    if not ObjectId.is_valid(inquiry_in.producer_id):
        raise HTTPException(status_code=400, detail="ID cantina non valido")
        
    producer = await db.producers.find_one({"_id": ObjectId(inquiry_in.producer_id)})
    if not producer:
        raise HTTPException(status_code=404, detail="Cantina non trovata")
        
    doc = inquiry_in.model_dump()
    doc["producer_id"] = ObjectId(inquiry_in.producer_id)
    
    if inquiry_in.product_id and ObjectId.is_valid(inquiry_in.product_id):
        doc["product_id"] = ObjectId(inquiry_in.product_id)
    else:
        doc["product_id"] = None
        
    doc["is_read"] = False
    doc["created_at"] = datetime.utcnow()
    
    res = await db.inquiries.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    doc["producer_id"] = str(doc["producer_id"])
    doc["producer_name"] = producer.get("company_name", "")
    
    if doc.get("product_id"):
        doc["product_id"] = str(doc["product_id"])
        prod = await db.products.find_one({"_id": ObjectId(doc["product_id"])})
        if prod:
            doc["product_name"] = prod.get("name", "")
            
    return doc

@router.get("", response_model=List[InquiryResponse])
async def list_inquiries(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    is_admin = current_user.get("role") == "ADMIN"
    user_producer_id = current_user.get("producer_id")
    
    query = {}
    if not is_admin:
        if not user_producer_id or not ObjectId.is_valid(user_producer_id):
            return []
        query["producer_id"] = ObjectId(user_producer_id)
        
    # Pre-fetch producer and product maps to eliminate N+1 queries
    producers = await db.producers.find().to_list(1000)
    producer_map = {str(p["_id"]): p.get("company_name", "") for p in producers}

    products = await db.products.find({}, {"name": 1}).to_list(1000)
    product_map = {str(p["_id"]): p.get("name", "") for p in products}

    cursor = db.inquiries.find(query).sort("created_at", -1)
    raw_inquiries = await cursor.to_list(1000)
    
    inquiries = []
    for doc in raw_inquiries:
        doc["id"] = str(doc["_id"])
        doc["producer_id"] = str(doc["producer_id"])
        doc["producer_name"] = producer_map.get(doc["producer_id"], "")
        
        if doc.get("product_id"):
            doc["product_id"] = str(doc["product_id"])
            doc["product_name"] = product_map.get(doc["product_id"], "")
        else:
            doc["product_name"] = ""
            
        inquiries.append(doc)
    return inquiries

@router.put("/{inquiry_id}/read")
async def mark_inquiry_as_read(
    inquiry_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
):
    if not ObjectId.is_valid(inquiry_id):
        raise HTTPException(status_code=400, detail="ID non valido")
        
    inquiry = await db.inquiries.find_one({"_id": ObjectId(inquiry_id)})
    if not inquiry:
        raise HTTPException(status_code=404, detail="Messaggio non trovato")
        
    is_admin = current_user.get("role") == "ADMIN"
    user_producer_id = current_user.get("producer_id")
    
    if not is_admin and str(inquiry["producer_id"]) != str(user_producer_id):
        raise HTTPException(status_code=403, detail="Non puoi accedere a questo messaggio")
        
    await db.inquiries.update_one({"_id": ObjectId(inquiry_id)}, {"$set": {"is_read": True}})
    return {"message": "Messaggio segnato come letto"}
