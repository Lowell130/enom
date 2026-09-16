from fastapi import APIRouter, Query
from app.db.mongodb import get_database
from typing import Dict, Any, List, Optional
import re
import asyncio

router = APIRouter()

@router.get("/summary")
async def get_report_summary(
    province: Optional[str] = Query(None, description="Filtro per provincia (CB, IS)"),
    denominazione: Optional[str] = Query(None, description="Filtro per denominazione"),
    is_organic: Optional[bool] = Query(None, description="Filtro per regime biologico")
) -> Dict[str, Any]:
    db = await get_database()

    # 1. Fetch raw data in parallel
    raw_products, producers, master_grapes, master_pairings, master_attributes = await asyncio.gather(
        db.products.find({"status": "PUBLISHED"}).to_list(1000),
        db.producers.find().to_list(1000),
        db.grapes.find().to_list(1000),
        db.pairings.find().to_list(1000),
        db.attributes.find().to_list(1000)
    )

    # If no published wines, fallback to all products
    if not raw_products:
        raw_products = await db.products.find().to_list(1000)

    # Lookup maps for producer address
    producer_province_map: Dict[str, str] = {}
    producer_city_map: Dict[str, str] = {}
    for pr in producers:
        pr_id = str(pr["_id"])
        addr = pr.get("address", {}) or {}
        prov = addr.get("province")
        city = addr.get("city")
        if prov and prov.strip():
            producer_province_map[pr_id] = prov.strip().upper()
        if city and city.strip():
            producer_city_map[pr_id] = city.strip().title()

    # Available filter options extracted from raw data
    available_denominations = sorted(list({
        p.get("denominazione") for p in raw_products if p.get("denominazione")
    }))
    available_provinces = sorted(list({
        producer_province_map.get(str(p.get("producer_id")))
        for p in raw_products if str(p.get("producer_id")) in producer_province_map
    }))

    # Helper function to check if product is organic (matches useOrganic.ts composable)
    def check_is_organic(p: dict) -> bool:
        if not p:
            return False

        if p.get("is_organic") is True or p.get("organic") is True:
            return True

        custom_attributes = p.get("custom_attributes", []) or []
        for attr in custom_attributes:
            if not attr or not attr.get("name") or not attr.get("value"):
                continue
            name = str(attr.get("name")).lower().strip()
            value = str(attr.get("value")).lower().strip()

            # 1. Attribute name is 'tipo' or 'tipo vino'
            if (name in ['tipo', 'tipo vino'] or ('tipo' in name and name != 'biotipo')) and 'biolog' not in name:
                if re.search(r'biologic', value) or re.search(r'\bbio\b', value):
                    return True

            # 2. Attribute name contains 'biolog', 'certificazione', 'coltivazione', 'agricoltura'
            if 'biolog' in name or name in ['certificazione', 'coltivazione', 'agricoltura']:
                if re.search(r'biologic', value) or re.search(r'\bbio\b', value) or value in ['sì', 'si', 'yes', 'presente']:
                    return True

            # 3. Attribute value matches exact organic terms
            if re.search(r'^vino biologico$', value) or re.search(r'^biologico$', value) or re.search(r'^biologica$', value) or re.search(r'^\s*bio\s*$', value):
                return True

        return False

    # Apply filters
    filtered_products = []
    for p in raw_products:
        p_prov = producer_province_map.get(str(p.get("producer_id")))
        p_den = p.get("denominazione")
        p_bio = check_is_organic(p)

        if province and p_prov != province.strip().upper():
            continue
        if denominazione and p_den != denominazione:
            continue
        if is_organic is not None and p_bio != is_organic:
            continue

        filtered_products.append(p)

    products = filtered_products

    # 2. Executive KPIs
    total_products = len(products)
    unique_producer_ids = {str(p.get("producer_id")) for p in products if p.get("producer_id")}
    total_producers_in_sample = len(unique_producer_ids) if unique_producer_ids else len(producers)
    total_grapes = len(master_grapes)
    total_pairings = len(master_pairings)

    alcohol_list = [p.get("alcohol_degrees") for p in products if p.get("alcohol_degrees") is not None]
    avg_alcohol = round(sum(alcohol_list) / len(alcohol_list), 1) if alcohol_list else 13.5

    vintage_years = [p.get("vintage_year") for p in products if p.get("vintage_year") is not None]
    min_year = min(vintage_years) if vintage_years else None
    max_year = max(vintage_years) if vintage_years else None

    # 3. Category Breakdown
    cat_counts: Dict[str, int] = {}
    for p in products:
        cat = p.get("category", "ALTRO")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    
    category_breakdown = [
        {"category": cat, "count": count, "percentage": round((count / total_products) * 100, 1) if total_products > 0 else 0}
        for cat, count in cat_counts.items()
    ]

    # 4. Denomination Breakdown (DOC, IGT, DOP)
    den_counts: Dict[str, int] = {}
    for p in products:
        den = p.get("denominazione", "Altro / Senza Denominazione")
        if not den:
            den = "Altro / Senza Denominazione"
        den_counts[den] = den_counts.get(den, 0) + 1

    denomination_breakdown = sorted([
        {"name": den, "count": count, "percentage": round((count / total_products) * 100, 1) if total_products > 0 else 0}
        for den, count in den_counts.items()
    ], key=lambda x: x["count"], reverse=True)

    # 5. Production Zones (City) Breakdown
    city_counts: Dict[str, int] = {}
    for p in products:
        c_name = None
        for attr in p.get("custom_attributes", []):
            if attr.get("name", "").lower() == "zona di produzione" and attr.get("value"):
                val = attr.get("value")
                city_match = re.search(r'([A-Za-z\s]+)\s*\((CB|IS)\)', val, re.IGNORECASE)
                if city_match:
                    c_name = city_match.group(1).strip().title()
                    break

        if not c_name:
            pr_id = str(p.get("producer_id"))
            c_name = producer_city_map.get(pr_id)

        if c_name:
            city_counts[c_name] = city_counts.get(c_name, 0) + 1

    zone_breakdown = sorted([
        {"city": city, "count": count}
        for city, count in city_counts.items()
    ], key=lambda x: x["count"], reverse=True)

    # 6. Grapes Popularity Breakdown
    grape_counts: Dict[str, int] = {}
    for p in products:
        varieties = p.get("grape_varieties", []) or []
        for g in varieties:
            clean_g = re.sub(r'\s*\d+%', '', g).strip()
            if clean_g:
                grape_counts[clean_g] = grape_counts.get(clean_g, 0) + 1

    top_grapes = sorted([
        {"name": g_name, "count": count, "percentage": round((count / total_products) * 100, 1) if total_products > 0 else 0}
        for g_name, count in grape_counts.items()
    ], key=lambda x: x["count"], reverse=True)

    # 7. Food Pairings Top List
    pairing_counts: Dict[str, int] = {}
    for p in products:
        pairings = p.get("food_pairings", []) or []
        for pair in pairings:
            p_clean = pair.strip()
            if p_clean:
                pairing_counts[p_clean] = pairing_counts.get(p_clean, 0) + 1

    top_pairings = sorted([
        {"name": p_name, "count": count}
        for p_name, count in pairing_counts.items()
    ], key=lambda x: x["count"], reverse=True)[:10]

    # 8. Technical Attributes & Wood vs Steel Analytics
    vinificazione_counts: Dict[str, int] = {}
    affinamento_counts: Dict[str, int] = {}
    allevamento_counts: Dict[str, int] = {}
    altitudine_counts: Dict[str, int] = {}
    formato_counts: Dict[str, int] = {}

    wood_count = 0
    steel_count = 0

    for p in products:
        p_tech_text = ""
        for attr in p.get("custom_attributes", []):
            aname = attr.get("name", "").lower().strip() if attr.get("name") else ""
            aval = attr.get("value", "").strip() if attr.get("value") else ""
            if not aval:
                continue

            p_tech_text += f" {aval.lower()}"

            if "vinificazione" in aname:
                vinificazione_counts[aval] = vinificazione_counts.get(aval, 0) + 1
            elif "affinamento" in aname:
                affinamento_counts[aval] = affinamento_counts.get(aval, 0) + 1
            elif "allevamento" in aname:
                allevamento_counts[aval] = allevamento_counts.get(aval, 0) + 1
            elif "altitudine" in aname:
                altitudine_counts[aval] = altitudine_counts.get(aval, 0) + 1
            elif "formato" in aname:
                formato_counts[aval] = formato_counts.get(aval, 0) + 1

        if any(w in p_tech_text for w in ["barrique", "legno", "botte", "rovere", "tonneau"]):
            wood_count += 1
        elif any(s in p_tech_text for s in ["acciaio", "vasca", "inox"]):
            steel_count += 1
        else:
            # Fallback estimation based on category (Reds often have wood, Whites/Sparkling steel)
            if p.get("category") == "VINO_ROSSO":
                wood_count += 1
            else:
                steel_count += 1

    total_wood_steel = wood_count + steel_count
    wood_pct = round((wood_count / total_wood_steel) * 100, 1) if total_wood_steel > 0 else 50.0
    steel_pct = round((steel_count / total_wood_steel) * 100, 1) if total_wood_steel > 0 else 50.0

    return {
        "kpis": {
            "total_products": total_products,
            "total_producers": total_producers_in_sample,
            "total_grapes": total_grapes,
            "total_pairings": total_pairings,
            "avg_alcohol_degrees": avg_alcohol,
            "min_vintage_year": min_year,
            "max_vintage_year": max_year
        },
        "filter_options": {
            "provinces": available_provinces,
            "denominations": available_denominations
        },
        "category_breakdown": category_breakdown,
        "denomination_breakdown": denomination_breakdown,
        "zone_breakdown": zone_breakdown,
        "top_grapes": top_grapes,
        "top_pairings": top_pairings,
        "technical_analytics": {
            "vinificazione": sorted([{"name": k, "count": v} for k, v in vinificazione_counts.items()], key=lambda x: x["count"], reverse=True)[:6],
            "affinamento": sorted([{"name": k, "count": v} for k, v in affinamento_counts.items()], key=lambda x: x["count"], reverse=True)[:6],
            "allevamento": sorted([{"name": k, "count": v} for k, v in allevamento_counts.items()], key=lambda x: x["count"], reverse=True)[:6],
            "altitudine": sorted([{"name": k, "count": v} for k, v in altitudine_counts.items()], key=lambda x: x["count"], reverse=True)[:6],
            "formato": sorted([{"name": k, "count": v} for k, v in formato_counts.items()], key=lambda x: x["count"], reverse=True)[:6]
        },
        "wood_vs_steel": {
            "wood_count": wood_count,
            "steel_count": steel_count,
            "wood_percentage": wood_pct,
            "steel_percentage": steel_pct
        }
    }
