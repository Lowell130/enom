"""'E' la tua cantina?': rivendicazione delle pagine create dall'amministratore."""
from tests.test_security import API, BaseTest, run


class ClaimTests(BaseTest):
    def setUp(self):
        super().setUp()
        res = run(self.db.producers.insert_one({
            "company_name": "CATABBO Cantine", "slug": "catabbo-cantine", "status": "APPROVED",
            "address": {"city": "San Martino in Pensilis"}, "contacts": {"email_contact": "info@catabbo.it"}}))
        self.cat = res.inserted_id

    def outbox(self, template):
        return [d for d in self.db.email_outbox.docs if d["template"] == template]

    def test_info_masks_the_email_and_hides_for_active_accounts(self):
        info = self.client.get(f"{API}/producers/catabbo-cantine/claim").json()
        self.assertEqual(info, {"claimable": True, "has_email": True, "masked_email": "i***@catabbo.it", "link_days": 14})
        # Cantina Uno ha gia' un accesso attivo
        self.assertFalse(self.client.get(f"{API}/producers/cantina-uno/claim").json()["claimable"])
        # le cantine non approvate non si rivendicano
        self.assertEqual(self.client.get(f"{API}/producers/cantina-attesa/claim").status_code, 404)

    def test_link_goes_only_to_the_email_already_on_the_site(self):
        r = self.client.post(f"{API}/producers/catabbo-cantine/claim/email", json={"email": "ladro@esempio.it"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIn("i***@catabbo.it", r.json()["message"])
        invites = self.outbox("invito_cantina")
        self.assertEqual([i["to"] for i in invites], [["info@catabbo.it"]])
        self.assertIn("/guida", invites[0]["text"])  # link alla guida passo passo
        user = run(self.db.users.find_one({"producer_id": self.cat}))
        self.assertEqual(user["email"], "info@catabbo.it")
        self.assertIsNone(user.get("activated_at"))
        self.assertEqual(self.db.activity_log.docs[-1]["action"], "producer.claim_link_sent")

    def test_link_limit_and_no_link_once_active(self):
        url = f"{API}/producers/catabbo-cantine/claim/email"
        for _ in range(3):
            self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(self.client.post(url).status_code, 429)
        self.assertEqual(self.client.post(f"{API}/producers/cantina-uno/claim/email").status_code, 400)

    def test_manual_request_reaches_admin_with_winery_details(self):
        r = self.client.post(f"{API}/contact/claim", json={
            "producer_id": str(self.cat), "name": "Denise Rossi", "role": "Titolare", "email": "denise@posta.it",
            "phone": "327 123 4567", "message": "L'email del sito non è più attiva.", "privacy_accepted": True})
        self.assertEqual(r.status_code, 200, r.text)
        to_admin = self.outbox("messaggio_sito_admin")[0]
        self.assertEqual(to_admin["to"], ["admin@test.it"])
        self.assertEqual(to_admin["reply_to"], "denise@posta.it")
        self.assertIn("CATABBO Cantine", to_admin["subject"])
        self.assertIn("327 123 4567", to_admin["text"])
        self.assertEqual(self.outbox("conferma_messaggio_sito")[0]["to"], ["denise@posta.it"])
        items = self.client.get(f"{API}/contact", headers=self.auth(self.admin_token)).json()
        self.assertEqual(items[0]["reason"], "RIVENDICAZIONE")
        self.assertEqual(items[0]["producer_slug"], "catabbo-cantine")
        self.assertEqual(items[0]["producer_account"], "none")
        # l'amministratore invita il nuovo indirizzo dopo aver verificato
        r = self.client.post(f"{API}/producers/{self.cat}/invite", json={"email": "denise@posta.it"},
                             headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.outbox("invito_cantina")[-1]["to"], ["denise@posta.it"])

    def test_manual_request_needs_phone_and_privacy(self):
        base = {"producer_id": str(self.cat), "name": "X", "email": "x@posta.it", "privacy_accepted": True}
        self.assertEqual(self.client.post(f"{API}/contact/claim", json=base).status_code, 422)
        self.assertEqual(self.client.post(f"{API}/contact/claim", json={**base, "phone": "3331234567",
                                                                        "privacy_accepted": False}).status_code, 422)

    def test_similar_names_at_registration(self):
        hits = self.client.get(f"{API}/producers/similar", params={"name": "Cantine Catabbo s.r.l."}).json()
        self.assertEqual(hits, [{"company_name": "CATABBO Cantine", "slug": "catabbo-cantine"}])
        self.assertEqual(self.client.get(f"{API}/producers/similar", params={"name": "Cantina"}).json(), [])
        self.assertEqual(self.client.get(f"{API}/producers/similar", params={"name": "Vigna Nuova"}).json(), [])
