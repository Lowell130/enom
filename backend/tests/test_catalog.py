"""Test del catalogo dopo la suddivisione di products.py in moduli."""
import io
import json
import unittest

from tests.test_security import BaseTest, API, run
from app.services.catalog import (
    clean_product_slug,
    clean_wine_title,
    generate_unique_product_slug,
    parse_denominazione_acronym,
)
from app.services.taxonomy import sync_custom_attributes_with_master, sync_grapes_with_master


class CatalogUnitTests(unittest.TestCase):
    def test_clean_wine_title(self):
        self.assertEqual(clean_wine_title("Tintilia del Molise DOC 2021"), "Tintilia del Molise")
        self.assertEqual(clean_wine_title("Biferno Rosso D.O.C."), "Biferno Rosso")

    def test_clean_product_slug(self):
        self.assertEqual(clean_product_slug("Tintilia del Molise DOC 2021"), "tintilia-del-molise")

    def test_parse_denominazione(self):
        self.assertEqual(parse_denominazione_acronym("Molise D.O.C.G."), "DOCG")
        self.assertEqual(parse_denominazione_acronym("Terre degli Osci IGT"), "IGT")
        self.assertEqual(parse_denominazione_acronym(""), "DOC")


class CatalogApiTests(BaseTest):
    def test_slug_collision_uses_producer_slug(self):
        slug = run(generate_unique_product_slug(self.db, "Tintilia Pubblicata", self.p2))
        self.assertEqual(slug, "tintilia-pubblicata-cantina-due")

    def test_taxonomy_sync(self):
        run(self.db.attributes.insert_one({"name": "Affinamento", "suggested_values": []}))
        run(sync_custom_attributes_with_master([{"name": "affinamento", "value": "12 mesi"}], self.db))
        attr = run(self.db.attributes.find_one({"name": "Affinamento"}))
        self.assertIn("12 mesi", attr["suggested_values"])
        run(sync_grapes_with_master(["Tintilia 100%"], self.db))
        self.assertIsNotNone(run(self.db.grapes.find_one({"name": "Tintilia"})))

    def test_export_routes_not_shadowed_by_identifier(self):
        r = self.client.get(f"{API}/products/export/json", headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(len(json.loads(r.content)), 4)
        r = self.client.get(f"{API}/products/export/excel", headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content[:2], b"PK")

    def test_export_admin_only(self):
        r = self.client.get(f"{API}/products/export/json", headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 403)

    def test_import_json_roundtrip(self):
        payload = json.dumps([{"name": "Rosato Nuovo 2023", "producer_id": str(self.p2), "slug": "biferno-rosso"}]).encode()
        r = self.client.post(f"{API}/products/import/json", files={"file": ("c.json", payload, "application/json")},
                             headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["created"], 1)
        doc = run(self.db.products.find_one({"name": "Rosato Nuovo"}))
        self.assertNotEqual(doc["slug"], "biferno-rosso")

    def test_import_excel_roundtrip(self):
        exported = self.client.get(f"{API}/products/export/excel", headers=self.auth(self.admin_token)).content
        r = self.client.post(f"{API}/products/import/excel", files={"file": ("c.xlsx", io.BytesIO(exported), "application/octet-stream")},
                             headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["updated"], 4)
        self.assertEqual(r.json()["errors"], 0)

    def test_cleanup_endpoint_admin_only(self):
        self.assertEqual(self.client.post(f"{API}/products/cleanup-slugs-and-titles", headers=self.auth(self.p1_token)).status_code, 403)
        self.assertEqual(self.client.post(f"{API}/products/cleanup-slugs-and-titles", headers=self.auth(self.admin_token)).status_code, 200)

    def test_create_update_delete_flow(self):
        r = self.client.post(f"{API}/products", json={"name": "Spumante Metodo Classico", "grape_varieties": ["Falanghina"]},
                             headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 200, r.text)
        pid = r.json()["id"]
        self.assertEqual(r.json()["producer_id"], str(self.p1))
        self.assertIsNotNone(run(self.db.grapes.find_one({"name": "Falanghina"})))
        r = self.client.put(f"{API}/products/{pid}", json={"name": "Spumante Brut"}, headers=self.auth(self.p1_token))
        self.assertEqual(r.json()["slug"], "spumante-brut")
        self.assertEqual(self.client.delete(f"{API}/products/{pid}", headers=self.auth(self.p2_token)).status_code, 403)
        self.assertEqual(self.client.delete(f"{API}/products/{pid}", headers=self.auth(self.p1_token)).status_code, 200)


if __name__ == "__main__":
    unittest.main()
