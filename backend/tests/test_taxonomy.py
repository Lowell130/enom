"""Rinomina di abbinamenti, vitigni e campi della scheda tecnica: il nuovo nome vale anche per i vini."""
import unittest

from bson import ObjectId

from tests.test_security import API, BaseTest, run
from app.services.taxonomy import _rename_attributes, _rename_grapes, _rename_pairings


class RenameHelpersTests(unittest.TestCase):
    def test_pairings_case_insensitive_and_deduplicated(self):
        values = ["Antipasti", "Risotti & Piatti Al Tartufo", "Risotti & Piatti al Tartufo"]
        self.assertEqual(_rename_pairings(values, "Risotti & Piatti al Tartufo", "Risotti & Tartufo"),
                         ["Antipasti", "Risotti & Tartufo"])

    def test_grapes_keep_percentage_and_ignore_longer_names(self):
        values = ["Moscato 60%", "Moscato Reale 40%", "Trebbiano", "Trebbiano del Molise"]
        self.assertEqual(_rename_grapes(values, "Moscato", "Moscato Bianco"),
                         ["Moscato Bianco 60%", "Moscato Reale 40%", "Trebbiano", "Trebbiano del Molise"])
        self.assertEqual(_rename_grapes(values, "Trebbiano", "Trebbiano Toscano")[2:],
                         ["Trebbiano Toscano", "Trebbiano del Molise"])

    def test_attributes_merge_when_new_name_already_present(self):
        values = [{"name": "Affinamento", "value": "12 mesi in barrique"},
                  {"name": "Maturazione", "value": "6 mesi in bottiglia"},
                  {"name": "Formato", "value": "750 ml"}]
        self.assertEqual(_rename_attributes(values, "maturazione", "Affinamento"), [
            {"name": "Affinamento", "value": "12 mesi in barrique; 6 mesi in bottiglia"},
            {"name": "Formato", "value": "750 ml"},
        ])


class RenameEndpointsTests(BaseTest):
    def setUp(self):
        super().setUp()
        run(self.db.products.update_one({"_id": self.pub1}, {"$set": {
            "food_pairings": ["Primi Piatti Al Sugo", "Antipasti"],
            "grape_varieties": ["Tintilia 85%", "Montepulciano 15%"],
            "custom_attributes": [{"name": "Zona di Produzione", "value": "Campobasso"}],
        }}))
        run(self.db.products.update_one({"_id": self.pub2}, {"$set": {
            "food_pairings": ["Primi Piatti al Sugo"], "grape_varieties": ["Tintilia"],
            "custom_attributes": [{"name": "zona di produzione", "value": "Larino"}],
        }}))
        self.pairing = run(self.db.pairings.insert_one({"name": "Primi Piatti al Sugo", "category": "PRIMI"})).inserted_id
        run(self.db.pairings.insert_one({"name": "Antipasti", "category": "APERITIVI"}))
        self.grape = run(self.db.grapes.insert_one({"name": "Tintilia", "category": "AUTOCTONO"})).inserted_id
        self.attr = run(self.db.attributes.insert_one({"name": "Zona di Produzione", "suggested_values": []})).inserted_id

    def put(self, path, body, token=None):
        return self.client.put(f"{API}/{path}", json=body, headers=self.auth(token or self.admin_token))

    def product(self, oid):
        return run(self.db.products.find_one({"_id": oid}))

    def test_rename_pairing_updates_wines(self):
        res = self.put(f"pairings/{self.pairing}", {"name": "Primi Piatti & Sughi"})
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["products_updated"], 2)
        self.assertEqual(self.product(self.pub1)["food_pairings"], ["Primi Piatti & Sughi", "Antipasti"])
        self.assertEqual(self.product(self.pub2)["food_pairings"], ["Primi Piatti & Sughi"])

    def test_rename_grape_keeps_percentages(self):
        res = self.put(f"grapes/{self.grape}", {"name": "Tintilia del Molise"})
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["products_updated"], 2)
        self.assertEqual(self.product(self.pub1)["grape_varieties"], ["Tintilia del Molise 85%", "Montepulciano 15%"])

    def test_rename_attribute_updates_wines(self):
        res = self.put(f"attributes/{self.attr}", {"name": "Zona"})
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["products_updated"], 2)
        self.assertEqual(self.product(self.pub2)["custom_attributes"], [{"name": "Zona", "value": "Larino"}])

    def test_rename_to_existing_name_is_refused(self):
        res = self.put(f"pairings/{self.pairing}", {"name": "antipasti"})
        self.assertEqual(res.status_code, 409)
        self.assertIn("Esiste già", res.json()["detail"])
        self.assertEqual(self.product(self.pub2)["food_pairings"], ["Primi Piatti al Sugo"])

    def test_changing_only_capitalisation_is_allowed(self):
        res = self.put(f"pairings/{self.pairing}", {"name": "Primi Piatti Al Sugo"})
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(self.product(self.pub2)["food_pairings"], ["Primi Piatti Al Sugo"])

    def test_empty_name_is_refused(self):
        self.assertEqual(self.put(f"grapes/{self.grape}", {"name": "   "}).status_code, 400)

    def test_only_admin_can_rename(self):
        self.assertEqual(self.put(f"grapes/{self.grape}", {"name": "X"}, token=self.p1_token).status_code, 403)

    def test_create_does_not_duplicate_with_different_case(self):
        res = self.client.post(f"{API}/grapes", json={"name": "tintilia"}, headers=self.auth(self.admin_token))
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["id"], str(self.grape))
        self.assertEqual(run(self.db.grapes.count_documents({})), 1)


class AsciiSlugTests(BaseTest):
    def test_slug_helpers_remove_accents(self):
        from app.core.utils import slugify
        from app.services.catalog import clean_product_slug
        self.assertEqual(slugify("Vietènn Tintilia"), "vietenn-tintilia")
        self.assertEqual(clean_product_slug("Chapeau à la Vie Rosé DOC 2021"), "chapeau-a-la-vie-rose")
        self.assertEqual(clean_product_slug("Molì Rosso Terre degli Osci"), "moli-rosso-terre-degli-osci")

    def test_new_wine_gets_ascii_slug(self):
        res = self.client.post(f"{API}/products", json={
            "name": "Egò Passito Bianco", "producer_id": str(self.p1), "category": "PASSITO",
        }, headers=self.auth(self.admin_token))
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["slug"], "ego-passito-bianco")

    def test_migration_fixes_existing_slugs_and_old_links_still_work(self):
        from app.services.catalog import migrate_ascii_slugs
        run(self.db.products.update_one({"_id": self.pub1}, {"$set": {"slug": "vietènn-tintilia"}}))
        # un vino con l'indirizzo gia' "occupato": serve il suffisso
        run(self.db.products.update_one({"_id": self.pub2}, {"$set": {"slug": "molì-rosso"}}))
        self._product("Moli Rosso", "moli-rosso", self.p2)
        self.assertEqual(run(migrate_ascii_slugs(self.db)), 2)
        self.assertEqual(run(self.db.products.find_one({"_id": self.pub1}))["slug"], "vietenn-tintilia")
        self.assertEqual(run(self.db.products.find_one({"_id": self.pub2}))["slug"], "moli-rosso-2")
        self.assertEqual(run(migrate_ascii_slugs(self.db)), 0)  # seconda esecuzione: nulla da fare
        # il vecchio link con l'accento porta ancora al vino
        res = self.client.get(f"{API}/products/vietènn-tintilia")
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["slug"], "vietenn-tintilia")
