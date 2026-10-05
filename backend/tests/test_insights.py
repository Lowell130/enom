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

    def test_temperature_normalized(self):
        self.assertEqual(ins.normalize_temperature_text("8 - 10°"), "8-10°C")
        self.assertEqual(ins.normalize_temperature_text("18°"), "18°C")
        self.assertEqual(ins.normalize_temperature_text("12,5°"), "12,5°C")
        self.assertEqual(ins.normalize_temperature_text("Scheda tecnica"), "")
        from app.schemas.product import ProductUpdate
        self.assertEqual(ProductUpdate(serving_temperature="10° - 12°").serving_temperature, "10-12°C")
        self.assertIsNone(ProductUpdate().serving_temperature)

    def test_normalize_catalog_script(self):
        import importlib.util, pathlib
        from tests.fake_mongo import FakeClient
        spec = importlib.util.spec_from_file_location("nc", pathlib.Path(__file__).parent.parent / "scripts" / "normalize_catalog.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        database = FakeClient()["t"]
        run_ = __import__("asyncio").run
        run_(database.products.insert_one({"name": "A", "indicative_price": "€14", "serving_temperature": "8 - 10°",
                                           "grape_varieties": ["Montepulciano 55% Sangiovese 45%"]}))
        run_(database.products.insert_one({"name": "B", "indicative_price": "14,00 €", "serving_temperature": "16-18°C",
                                           "grape_varieties": ["Tintilia 100%"]}))
        self.assertEqual(run_(mod.normalize_catalog(database, apply=False)), 1)
        self.assertEqual(run_(database.products.find_one({"name": "A"}))["indicative_price"], "€14")  # anteprima
        self.assertEqual(run_(mod.normalize_catalog(database, apply=True)), 1)
        a = run_(database.products.find_one({"name": "A"}))
        self.assertEqual((a["indicative_price"], a["serving_temperature"], a["grape_varieties"]),
                         ("14,00 €", "8-10°C", ["Montepulciano 55%", "Sangiovese 45%"]))

    def test_multi_grape_entry_split(self):
        self.assertEqual(ins.split_grape_entry("Montepulciano 55% Sangiovese 45%"), ["Montepulciano 55%", "Sangiovese 45%"])
        self.assertEqual(ins.split_grape_entry("Montepulciano 85% - Aglianico 15%"), ["Montepulciano 85%", "Aglianico 15%"])
        self.assertEqual(ins.split_grape_entry("Tintilia 100%"), ["Tintilia 100%"])
        self.assertEqual(ins.split_grape_entry("Coda di Volpe"), ["Coda di Volpe"])
        self.assertEqual(ins.split_grape_entry("Montepulciano in Purezza"), ["Montepulciano 100%"])
        from app.schemas.product import ProductCreate, ProductUpdate
        self.assertEqual(ProductCreate(name="X", grape_varieties=["Montepulciano 55% Sangiovese 45%"]).grape_varieties,
                         ["Montepulciano 55%", "Sangiovese 45%"])
        self.assertIsNone(ProductUpdate().grape_varieties)

    def test_import_keeps_every_grape(self):
        from app.services.pdf_importer import normalize_grapes
        master = ["Montepulciano", "Sangiovese", "Falanghina", "Greco"]
        self.assertEqual(normalize_grapes(["Montepulciano 55% Sangiovese 45%"], master)[0], ["Montepulciano", "Sangiovese"])
        self.assertEqual(normalize_grapes(["Falanghina e Greco"], master)[0], ["Falanghina", "Greco"])
        self.assertEqual(normalize_grapes(["Montepulciano in purezza"], master), (["Montepulciano"], "Montepulciano 100%"))
        # "Moscato Bianco" e' ricondotto a "Moscato" (non e' piu' una voce a se')
        self.assertEqual(normalize_grapes(["Moscato Bianco 95%"], ["Moscato"])[0], ["Moscato"])

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


class AdminCountsTests(BaseTest):
    def test_stats_match_public_catalog_and_flag_orphans(self):
        from bson import ObjectId
        # vino collegato (come testo) a una cantina esistente e vino di una cantina che non esiste piu'
        self._product("Vino Collegato Come Testo", "vino-testo", str(self.p1))
        self._product("Vino Orfano", "vino-orfano", ObjectId())
        r = self.client.get(f"{API}/admin/stats", headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200, r.text)
        stats = r.json()
        self.assertEqual(stats["orphan_products"], 1)
        # pubblicati come nel catalogo: niente bozze, niente cantine in attesa, niente orfani
        public = self.client.get(f"{API}/products").json()
        self.assertEqual(stats["published_products"], len(public))
        self.assertIn("vino-testo", [w["slug"] for w in public])
        self.assertEqual(stats["total_products"], 5)

    def test_deleting_winery_removes_wines_linked_as_text(self):
        self._product("Vino Collegato Come Testo", "vino-testo", str(self.p2))
        r = self.client.delete(f"{API}/producers/{self.p2}", headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(run(self.db.products.count_documents({"producer_id": {"$in": [self.p2, str(self.p2)]}})), 0)

    def test_deleting_winery_removes_inquiries_and_accounts(self):
        run(self.db.inquiries.insert_one({"producer_id": self.p2, "user_name": "X", "message": "ciao"}))
        run(self.db.users.insert_one({"email": "cantina2@example.com", "role": "PRODUCER", "producer_id": self.p2}))
        r = self.client.delete(f"{API}/producers/{self.p2}", headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertGreaterEqual(r.json()["accounts_deleted"], 1)
        self.assertEqual(run(self.db.inquiries.count_documents({"producer_id": self.p2})), 0)
        self.assertEqual(run(self.db.users.count_documents({"producer_id": self.p2})), 0)
        self.assertGreater(run(self.db.users.count_documents({"role": "ADMIN"})), 0)
