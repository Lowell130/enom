"""Test degli approfondimenti dell'Osservatorio e dell'area riservata."""
import unittest
from datetime import datetime

from tests.test_security import BaseTest, API, run
from app.services import insights as ins


def wine(name, category="VINO_ROSSO", grapes=("Tintilia",), attrs=None, **extra):
    doc = {
        "name": name, "slug": name.lower().replace(" ", "-"), "category": category,
        "grape_varieties": list(grapes), "producer_id": extra.pop("producer_id", "p1"),
        "custom_attributes": [{"name": k, "value": v} for k, v in (attrs or {}).items()],
    }
    doc.update(extra)
    return doc


class ParserTests(unittest.TestCase):
    def test_harvest_months(self):
        self.assertEqual(ins.parse_harvest_months("Ultima decade di settembre"), [9])
        self.assertEqual(ins.parse_harvest_months("Fine agosto/inizio settembre"), [8, 9])
        self.assertEqual(ins.parse_harvest_months("da settembre a novembre"), [9, 10, 11])
        # "settimana" non va scambiata per "set(tembre)"
        self.assertEqual(ins.parse_harvest_months("Seconda settimana di ottobre"), [10])
        self.assertEqual(ins.parse_harvest_months("Manuale"), [])

    def test_altitude(self):
        self.assertEqual(ins.parse_altitude("300/350 mt"), 325)
        self.assertEqual(ins.parse_altitude("500m s.l.m."), 500)
        self.assertEqual(ins.parse_altitude("100-120 mt"), 110)
        self.assertEqual(ins.parse_altitude("1.200 m"), 1200)
        self.assertIsNone(ins.parse_altitude("collina"))

    def test_price(self):
        self.assertEqual(ins.parse_price("17,00 €"), 17.0)
        self.assertEqual(ins.parse_price("€14,00"), 14.0)
        self.assertEqual(ins.parse_price("35,00€ - 55,00€"), 45.0)
        self.assertEqual(ins.parse_price("1.200,00 €"), 1200.0)
        self.assertIsNone(ins.parse_price("su richiesta"))

    def test_price_text_normalized(self):
        self.assertEqual(ins.normalize_price_text("€14,00"), "14,00 €")
        self.assertEqual(ins.normalize_price_text("35,00€ - 55,00€"), "35,00 – 55,00 €")
        self.assertEqual(ins.normalize_price_text("12"), "12,00 €")
        self.assertEqual(ins.normalize_price_text("su richiesta"), "su richiesta")
        self.assertEqual(ins.normalize_price_text("15 € in cantina"), "15 € in cantina")
        self.assertEqual(ins.normalize_price_text(""), "")

    def test_price_normalized_when_saving(self):
        from app.schemas.product import ProductCreate, ProductUpdate
        self.assertEqual(ProductCreate(name="X", indicative_price="€ 8,5").indicative_price, "8,50 €")
        self.assertEqual(ProductUpdate(indicative_price="21€-41€").indicative_price, "21,00 – 41,00 €")
        self.assertIsNone(ProductUpdate().indicative_price)
        self.assertEqual(ins.format_price(17), "17,00 €")

    def test_temperature_and_soils(self):
        self.assertEqual(ins.parse_temperature("16-18°C"), (16.0, 18.0))
        self.assertEqual(ins.parse_temperature("10°-12°C"), (10.0, 12.0))
        self.assertEqual(ins.parse_soils("Argilloso - Calcareo, ricco di scheletro"), ["Argilloso", "Calcareo", "Ricco di scheletro"])

    def test_grape_groups(self):
        self.assertEqual(ins.product_grape_group(wine("a", grapes=["Tintilia 85%", "Merlot 15%"])), "tintilia")
        self.assertEqual(ins.product_grape_group(wine("b", grapes=["Montepulciano", "Cabernet Sauvignon"])), "international")
        self.assertEqual(ins.product_grape_group(wine("c", grapes=["Falanghina"])), "traditional")
        self.assertEqual(ins.product_grape_group(wine("d", grapes=[])), "other")


class AggregateTests(unittest.TestCase):
    def setUp(self):
        self.wines = [
            wine("Rosso Alto", attrs={"Periodo Raccolta": "Ottobre", "Altitudine Vigneto": "700 mt", "Tipologia Terreno": "Argilloso"},
                 serving_temperature="16-18°C", alcohol_degrees=14, indicative_price="30,00 €", food_pairings=["Arrosti"]),
            wine("Rosso Basso", grapes=["Montepulciano"], attrs={"Periodo Raccolta": "Settembre - Ottobre", "Altitudine Vigneto": "100 m"},
                 serving_temperature="18-20°C", alcohol_degrees=13, indicative_price="€12,00", food_pairings=["Arrosti"], producer_id="p2"),
            wine("Bianco", category="VINO_BIANCO", grapes=["Falanghina"], attrs={"Periodo Raccolta": "Settembre", "Tipologia Terreno": "Sabbioso"},
                 serving_temperature="8-10°C", alcohol_degrees=12.5, food_pairings=["Pesce"]),
        ]

    def test_harvest_calendar(self):
        cal = ins.harvest_calendar(self.wines)
        self.assertEqual(cal["wines_with_data"], 3)
        self.assertEqual([m["month"] for m in cal["months"]], [9, 10])
        tintilia = next(g for g in cal["grapes"] if g["grape"] == "Tintilia")
        self.assertEqual([m["count"] for m in tintilia["months"]], [0, 1])

    def test_altitude_profile(self):
        alt = ins.altitude_profile(self.wines, min_wines_per_grape=1)
        self.assertEqual(alt["wines_with_data"], 2)
        self.assertEqual(alt["highest"]["name"], "Rosso Alto")
        self.assertEqual(alt["grapes"][0]["grape"], "Tintilia")
        bands = {b["label"]: b["count"] for b in alt["bands"]}
        self.assertEqual(bands["Fino a 200 m"], 1)
        self.assertEqual(bands["Oltre 600 m"], 1)

    def test_serving_prices_pairings(self):
        guide = {g["category"]: g for g in ins.serving_guide(self.wines)}
        self.assertEqual(guide["VINO_BIANCO"]["temp_min"], 8)
        self.assertEqual(guide["VINO_ROSSO"]["wines"], 2)
        prices = ins.price_profile(self.wines)
        self.assertEqual(prices["wines_with_price"], 2)
        self.assertEqual(prices["median"], 21.0)
        pairings = ins.pairing_guide(self.wines)
        self.assertEqual(pairings[0]["pairing"], "Arrosti")
        self.assertEqual(len(pairings[0]["examples"]), 2)  # due cantine diverse

    def test_completeness(self):
        rep = ins.completeness_report(self.wines)
        self.assertEqual(rep["wines"], 3)
        self.assertEqual(rep["complete"], 0)
        self.assertTrue(all("Foto" in r["missing"] for r in rep["to_improve"]))
        # l'annata e' mostrata ma non conta per la completezza
        self.assertTrue(all("Annata" not in r["missing"] for r in rep["to_improve"]))
        self.assertTrue(next(f for f in rep["fields"] if f["field"] == "vintage_year")["optional"])


class InsightsApiTests(BaseTest):
    def test_public_insights(self):
        run(self.db.products.update_one({"_id": self.pub1}, {"$set": {
            "grape_varieties": ["Tintilia"], "serving_temperature": "16-18°C", "indicative_price": "20,00 €",
            "custom_attributes": [{"name": "Periodo Raccolta", "value": "Ottobre"}, {"name": "Zona di Produzione", "value": "Larino (CB)"},
                                  {"name": "Altitudine Vigneto", "value": "450 mt"}],
        }}))
        r = self.client.get(f"{API}/reports/insights")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        # bozze e vini di cantine non approvate esclusi
        self.assertEqual(body["wines"], 2)
        self.assertEqual(body["harvest"]["months"][0]["label"], "Ottobre")
        towns = {t["city"]: t for t in body["towns"]}
        self.assertIn("Larino", towns)
        self.assertEqual(towns["Larino"]["producers"][0]["company_name"], "Cantina Uno")
        self.assertEqual(body["prices"]["wines_with_price"], 1)
        # gli esempi riportano il nome della cantina, che non e' salvato nella scheda
        self.assertEqual(body["altitude"]["highest"]["producer"], "Cantina Uno")

    def test_private_requires_login(self):
        r = self.client.get(f"{API}/reports/private")
        self.assertEqual(r.status_code, 401)

    def test_private_scoped_to_producer(self):
        run(self.db.inquiries.insert_one({"producer_id": self.p1, "product_id": self.pub1, "message_type": "INFO_PREZZI",
                                          "is_read": False, "created_at": datetime.utcnow()}))
        run(self.db.inquiries.insert_one({"producer_id": self.p2, "product_id": self.pub2, "message_type": "ALTRO",
                                          "is_read": True, "created_at": datetime.utcnow()}))
        r = self.client.get(f"{API}/reports/private", headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["completeness"]["wines"], 2)  # pubblicato + bozza della propria cantina
        self.assertEqual(body["inquiries"]["total"], 1)
        self.assertEqual(body["inquiries"]["top_wines"][0]["name"], "Tintilia Pubblicata")

        r = self.client.get(f"{API}/reports/private", headers=self.auth(self.admin_token))
        self.assertEqual(r.json()["inquiries"]["total"], 2)
        self.assertEqual(r.json()["completeness"]["wines"], 4)


if __name__ == "__main__":
    unittest.main()
