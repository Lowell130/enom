"""Contatti con le cantine: storico dei contatti, cantine fuori dal sito, promemoria."""
from datetime import date, datetime, timedelta

from tests.test_security import API, BaseTest, run


class OutreachTests(BaseTest):
    def get(self):
        r = self.client.get(f"{API}/outreach", headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200, r.text)
        return {i["name"]: i for i in r.json()["items"]}

    def setUp(self):
        super().setUp()
        self.nuova = self._producer("Cantina Nuova", "cantina-nuova")  # nessun accesso
        self.A = self.auth(self.admin_token)

    def test_admin_only(self):
        self.assertEqual(self.client.get(f"{API}/outreach").status_code, 401)
        self.assertEqual(self.client.get(f"{API}/outreach", headers=self.auth(self.p1_token)).status_code, 403)
        r = self.client.post(f"{API}/outreach/prospects", json={"name": "X Cantina"}, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 403)

    def test_never_contacted_is_to_do_and_active_is_not(self):
        items = self.get()
        self.assertTrue(items["Cantina Nuova"]["to_do"])
        self.assertIsNone(items["Cantina Nuova"]["last_contact_at"])
        self.assertEqual(items["Cantina Uno"]["account"], "active")
        self.assertFalse(items["Cantina Uno"]["to_do"])

    def test_log_contact_then_reminder_after_a_week(self):
        r = self.client.post(f"{API}/outreach/log", headers=self.A, json={
            "target_type": "producer", "target_id": str(self.nuova), "channel": "WHATSAPP",
            "note": "Messaggio su WhatsApp, nessuna risposta"})
        self.assertEqual(r.status_code, 200, r.text)
        item = self.get()["Cantina Nuova"]
        self.assertFalse(item["to_do"])
        self.assertTrue(item["waiting"])
        self.assertEqual(item["history"][0]["channel_label"], "WhatsApp")
        # un contatto di 10 giorni fa: va risentita
        log_id = item["history"][0]["id"]
        self.client.delete(f"{API}/outreach/log/{log_id}", headers=self.A)
        old = (date.today() - timedelta(days=10)).isoformat()
        self.client.post(f"{API}/outreach/log", headers=self.A, json={
            "target_type": "producer", "target_id": str(self.nuova), "channel": "EMAIL", "contacted_on": old})
        item = self.get()["Cantina Nuova"]
        self.assertTrue(item["to_do"])
        self.assertEqual(len(item["history"]), 1)

    def test_site_invite_counts_as_contact(self):
        r = self.client.post(f"{API}/producers/{self.nuova}/invite", json={"email": "info@cantinanuova.it"}, headers=self.A)
        self.assertEqual(r.status_code, 200, r.text)
        item = self.get()["Cantina Nuova"]
        self.assertEqual(item["account"], "invited")
        self.assertTrue(item["history"][0]["auto"])
        self.assertTrue(item["waiting"])

    def test_prospect_lifecycle_and_link_when_registered(self):
        r = self.client.post(f"{API}/outreach/prospects", headers=self.A, json={
            "name": "Cantina Cliternia", "city": "Campomarino", "facebook": "https://facebook.com/cliternia",
            "notes": "Trovata su Facebook"})
        self.assertEqual(r.status_code, 200, r.text)
        sid = r.json()["id"]
        item = self.get()["Cantina Cliternia"]
        self.assertEqual(item["kind"], "prospect")
        self.assertEqual(item["status"], "DA_CONTATTARE")
        self.assertTrue(item["to_do"])
        self.client.post(f"{API}/outreach/log", headers=self.A, json={
            "target_type": "prospect", "target_id": sid, "channel": "FACEBOOK", "note": "Messaggio su Messenger"})
        item = self.get()["Cantina Cliternia"]
        self.assertEqual(item["status"], "CONTATTATA")
        self.assertIsNone(item["maybe_registered"])
        # si iscrive con un nome simile: suggerimento e collegamento
        cl = self._producer("Cliternia s.r.l.", "cliternia")
        self.assertEqual(self.get()["Cantina Cliternia"]["maybe_registered"]["id"], str(cl))
        r = self.client.post(f"{API}/outreach/prospects/{sid}/link", headers=self.A, json={"producer_id": str(cl)})
        self.assertEqual(r.status_code, 200, r.text)
        items = self.get()
        self.assertNotIn("Cantina Cliternia", items)
        notes = [h["note"] for h in items["Cliternia s.r.l."]["history"]]
        self.assertIn("Messaggio su Messenger", notes)
        self.assertTrue(any("Trovata su Facebook" in n for n in notes))

    def test_not_interested_is_not_to_do_and_delete_removes_history(self):
        sid = self.client.post(f"{API}/outreach/prospects", headers=self.A, json={"name": "Vigna Lontana"}).json()["id"]
        r = self.client.put(f"{API}/outreach/prospects/{sid}", headers=self.A,
                            json={"name": "Vigna Lontana", "status": "NON_INTERESSATA"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertFalse(self.get()["Vigna Lontana"]["to_do"])
        self.client.post(f"{API}/outreach/log", headers=self.A, json={"target_type": "prospect", "target_id": sid})
        self.client.delete(f"{API}/outreach/prospects/{sid}", headers=self.A)
        self.assertNotIn("Vigna Lontana", self.get())
        self.assertEqual(run(self.db.outreach_log.count_documents({})), 0)

    def test_incomplete_profile_filter(self):
        items = self.get()
        uno = items["Cantina Uno"]  # accesso attivo, senza logo, foto, storia, mappa
        self.assertTrue(uno["incomplete"])
        self.assertIn("logo", uno["missing"])
        self.assertIn("posizione sulla mappa", uno["missing"])
        self.assertNotIn("vini", uno["missing"])  # ha un vino
        self.assertFalse(items["Cantina Nuova"]["incomplete"])  # senza accesso: e' tra quelle da invitare
        run(self.db.producers.update_one({"_id": self.p1}, {"$set": {
            "logo_url": "/uploads/l.jpg", "cover_image_url": "/uploads/c.jpg", "description": "x" * 160,
            "address": {"city": "Campobasso", "geo_coordinates": {"lat": 41.5, "lng": 14.6}},
            "contacts": {"phone": "0874 1"}}}))
        uno = self.get()["Cantina Uno"]
        self.assertEqual(uno["missing"], [])
        self.assertFalse(uno["incomplete"])

    def test_future_date_rejected(self):
        future = (date.today() + timedelta(days=5)).isoformat()
        r = self.client.post(f"{API}/outreach/log", headers=self.A, json={
            "target_type": "producer", "target_id": str(self.nuova), "contacted_on": future})
        self.assertEqual(r.status_code, 422)

    def test_deleting_winery_removes_its_contacts(self):
        self.client.post(f"{API}/outreach/log", headers=self.A, json={"target_type": "producer", "target_id": str(self.nuova)})
        r = self.client.delete(f"{API}/producers/{self.nuova}", headers=self.A)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(run(self.db.outreach_log.count_documents({})), 0)
