"""Valori pronti dei campi della scheda tecnica: uso nei vini e unificazione dei doppioni."""
from tests.test_security import API, BaseTest, run


class AttributeValuesTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.attr = run(self.db.attributes.insert_one({
            "name": "Altitudine Vigneto", "unit_or_hint": "",
            "suggested_values": ["300m slm", "300 m s.l.m.", "500 m s.l.m."]})).inserted_id
        run(self.db.products.update_one({"_id": self.pub1}, {"$set": {"custom_attributes": [
            {"name": "altitudine vigneto", "value": "300m slm"}, {"name": "Affinamento", "value": "12 mesi"}]}}))
        run(self.db.products.update_one({"_id": self.draft1}, {"$set": {"custom_attributes": [
            {"name": "Altitudine Vigneto", "value": "300 m s.l.m. "}]}}))

    def test_usage_counts_values(self):
        r = self.client.get(f"{API}/attributes/usage", headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()[str(self.attr)], {"300m slm": 1, "300 m s.l.m.": 1})
        # solo l'amministratore
        self.assertEqual(self.client.get(f"{API}/attributes/usage", headers=self.auth(self.p1_token)).status_code, 403)

    def test_unify_rewrites_wines_and_presets(self):
        r = self.client.post(f"{API}/attributes/{self.attr}/unify-values", headers=self.auth(self.admin_token),
                             json={"target": "300 m s.l.m.", "sources": ["300m slm", "300 m s.l.m."]})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["products_updated"], 1)  # l'altro vino aveva gia' il valore scelto
        p = run(self.db.products.find_one({"_id": self.pub1}))
        self.assertEqual(p["custom_attributes"][0]["value"], "300 m s.l.m.")
        self.assertEqual(p["custom_attributes"][1]["value"], "12 mesi")  # gli altri campi non cambiano
        attr = run(self.db.attributes.find_one({"_id": self.attr}))
        self.assertEqual(attr["suggested_values"], ["300 m s.l.m.", "500 m s.l.m."])
        usage = self.client.get(f"{API}/attributes/usage", headers=self.auth(self.admin_token)).json()
        self.assertEqual(usage[str(self.attr)], {"300 m s.l.m.": 2})
