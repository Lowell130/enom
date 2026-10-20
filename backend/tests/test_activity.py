"""Registro delle attività delle cantine (area admin)."""
from tests.test_security import API, BaseTest, run


class ActivityLogTests(BaseTest):
    def log(self, action=None):
        docs = sorted(self.db.activity_log.docs, key=lambda d: d["created_at"])
        return [d for d in docs if action is None or d["action"] == action]

    def test_profile_change_is_logged_with_before_and_after(self):
        r = self.client.put(f"{API}/producers/{self.p1}", headers=self.auth(self.p1_token), json={
            "contacts": {"phone": "3357658942"}, "description": "Una storia lunga " * 20})
        self.assertEqual(r.status_code, 200, r.text)
        entry = self.log("producer.updated")[0]
        self.assertEqual(entry["producer_name"], "Cantina Uno")
        self.assertEqual(entry["user_email"], "uno@test.it")
        changes = {c["field"]: c for c in entry["changes"]}
        self.assertEqual(changes["contacts.phone"]["after"], "3357658942")
        # i testi lunghi non vengono copiati nel registro
        self.assertEqual(changes["description"], {"field": "description", "label": "Storia", "note": "aggiunto"})

    def test_admin_changes_are_not_logged(self):
        self.client.put(f"{API}/producers/{self.p1}", headers=self.auth(self.admin_token), json={"company_name": "Nuovo"})
        self.client.put(f"{API}/products/{self.pub1}", headers=self.auth(self.admin_token), json={"name": "Altro"})
        self.assertEqual(self.log(), [])

    def test_wine_create_update_delete_and_empty_save(self):
        h = self.auth(self.p1_token)
        r = self.client.post(f"{API}/products", headers=h, json={
            "name": "Falanghina Nuova", "category": "VINO_BIANCO", "denominazione": "DOC", "status": "DRAFT"})
        self.assertEqual(r.status_code, 200, r.text)
        pid = r.json()["id"]
        self.client.put(f"{API}/products/{pid}", headers=h, json={"status": "PUBLISHED", "alcohol_degrees": 12.5})
        self.client.put(f"{API}/products/{pid}", headers=h, json={"alcohol_degrees": 12.5})  # nessun cambiamento
        self.client.delete(f"{API}/products/{pid}", headers=h)
        actions = [d["action"] for d in self.log()]
        self.assertEqual(actions, ["product.created", "product.updated", "product.deleted"])
        status = next(c for c in self.log("product.updated")[0]["changes"] if c["field"] == "status")
        self.assertEqual((status["before"], status["after"]), ("Bozza", "Pubblicato"))
        self.assertEqual(self.log("product.deleted")[0]["target_name"], "Falanghina Nuova")

    def test_login_is_logged_at_most_once_every_few_hours(self):
        for _ in range(2):
            r = self.client.post(f"{API}/auth/login", json={"email": "uno@test.it", "password": "Password123!"})
            self.assertEqual(r.status_code, 200, r.text)
        self.client.post(f"{API}/auth/login", json={"email": "admin@test.it", "password": "Password123!"})
        self.assertEqual(len(self.log("account.login")), 1)

    def test_only_admin_reads_and_filters(self):
        h = self.auth(self.p1_token)
        self.client.put(f"{API}/producers/{self.p1}", headers=h, json={"contacts": {"phone": "1"}})
        self.client.put(f"{API}/products/{self.pub1}", headers=h, json={"name": "Tintilia Rinominata"})
        self.client.put(f"{API}/products/{self.pub2}", headers=self.auth(self.p2_token), json={"name": "Biferno Nuovo"})
        url = f"{API}/activity"
        self.assertEqual(self.client.get(url, headers=h).status_code, 403)
        admin = self.auth(self.admin_token)
        everything = self.client.get(url, headers=admin).json()
        self.assertEqual(len(everything["items"]), 3)
        self.assertEqual(everything["items"][0]["producer_name"], "Cantina Due")  # piu' recente prima
        only_p1 = self.client.get(url, params={"producer_id": str(self.p1)}, headers=admin).json()["items"]
        self.assertEqual({i["producer_name"] for i in only_p1}, {"Cantina Uno"})
        wines = self.client.get(url, params={"group": "product"}, headers=admin).json()["items"]
        self.assertEqual(len(wines), 2)
        self.assertEqual(wines[0]["target_slug"], run(self.db.products.find_one({"_id": self.pub2}))["slug"])
        page = self.client.get(url, params={"limit": 2}, headers=admin).json()
        self.assertTrue(page["has_more"])
        rest = self.client.get(url, params={"limit": 2, "before": page["items"][-1]["created_at"]}, headers=admin).json()
        self.assertEqual(len(rest["items"]), 1)
