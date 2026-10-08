"""Esperienza delle cantine: registrazione, email (posta in uscita), recupero password, approvazione,
richieste dei clienti, cancellazione, modelli email e testi del sito."""
import re
from datetime import datetime, timedelta

from tests.test_security import API, BaseTest, run
from app.core.config import settings
from app.services import email as mail


def register(client, email="nuova@cantina.it", **extra):
    body = {"email": email, "password": "Password123!", "company_name": "Cantina Nuova", "privacy_accepted": True}
    body.update(extra)
    return client.post(f"{API}/auth/register", json=body)


class EmailTestBase(BaseTest):
    def outbox(self, template=None):
        docs = sorted(self.db.email_outbox.docs, key=lambda d: d["created_at"])
        return [d for d in docs if template is None or d["template"] == template]


class RegistrationTests(EmailTestBase):
    def test_registration_sends_welcome_and_admin_notice(self):
        r = register(self.client)
        self.assertEqual(r.status_code, 200, r.text)
        welcome = self.outbox("registrazione_cantina")
        self.assertEqual(len(welcome), 1)
        self.assertEqual(welcome[0]["to"], ["nuova@cantina.it"])
        self.assertEqual(welcome[0]["status"], "outbox")  # sviluppo: nessun invio reale
        self.assertIn("Cantina Nuova", welcome[0]["subject"])
        self.assertIn(settings.SITE_URL + "/dashboard", welcome[0]["html"])
        admin_notice = self.outbox("nuova_cantina_admin")
        self.assertEqual(admin_notice[0]["to"], ["admin@test.it"])

    def test_no_default_city(self):
        register(self.client)
        user = run(self.db.users.find_one({"email": "nuova@cantina.it"}))
        producer = run(self.db.producers.find_one({"_id": user["producer_id"]}))
        self.assertEqual(producer["address"]["city"], "")
        self.assertIsNotNone(user["privacy_accepted_at"])

    def test_privacy_is_required_with_readable_message(self):
        r = register(self.client, privacy_accepted=False)
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["detail"], "Per registrarti devi accettare l'informativa sulla privacy")
        r = self.client.post(f"{API}/auth/register", json={"email": "x@cantina.it", "password": "Password123!"})
        self.assertEqual(r.status_code, 422)
        self.assertIn("privacy", r.json()["detail"])

    def test_invalid_email_has_readable_message(self):
        r = register(self.client, email="prova@cantina.test")
        self.assertEqual(r.status_code, 422)
        self.assertIn("L'indirizzo email non è valido", r.json()["detail"])
        r = register(self.client, password="corta")
        self.assertIn("Password: almeno 8 caratteri", r.json()["detail"])

    def test_disabled_template_is_not_sent(self):
        run(self.db.email_templates.insert_one({"key": "registrazione_cantina", "enabled": False}))
        register(self.client)
        self.assertEqual(self.outbox("registrazione_cantina"), [])
        self.assertEqual(len(self.outbox("nuova_cantina_admin")), 1)

    def test_admin_recipients_from_settings(self):
        run(self.db.site_settings.insert_one({"_id": "email", "admin_recipients": ["notifiche@portale.it"]}))
        register(self.client)
        self.assertEqual(self.outbox("nuova_cantina_admin")[0]["to"], ["notifiche@portale.it"])


class ApprovalTests(EmailTestBase):
    def test_approval_and_suspension_emails(self):
        h = self.auth(self.admin_token)
        r = self.client.put(f"{API}/producers/{self.p_pending}", json={"status": "APPROVED"}, headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        approved = self.outbox("cantina_approvata")
        self.assertEqual(approved[0]["to"], ["attesa@test.it"])
        self.assertIn("/produttori/cantina-attesa", approved[0]["html"])
        # salvare di nuovo senza cambiare stato non rimanda l'email
        self.client.put(f"{API}/producers/{self.p_pending}", json={"status": "APPROVED", "description": "x"}, headers=h)
        self.assertEqual(len(self.outbox("cantina_approvata")), 1)
        self.client.put(f"{API}/producers/{self.p_pending}", json={"status": "SUSPENDED"}, headers=h)
        self.assertEqual(len(self.outbox("cantina_sospesa")), 1)

    def test_producer_cannot_approve_itself(self):
        self.client.put(f"{API}/producers/{self.p_pending}", json={"status": "APPROVED"}, headers=self.auth(self.pending_token))
        self.assertEqual(run(self.db.producers.find_one({"_id": self.p_pending}))["status"], "PENDING_APPROVAL")
        self.assertEqual(self.outbox("cantina_approvata"), [])

    def test_admin_stats_count_pending_and_deletions(self):
        self.client.post(f"{API}/producers/me/deletion-request", json={"reason": "Chiudiamo"}, headers=self.auth(self.p2_token))
        stats = self.client.get(f"{API}/admin/stats", headers=self.auth(self.admin_token)).json()
        self.assertEqual(stats["pending_producers"], 1)
        self.assertEqual(stats["deletion_requests"], 1)


class InquiryEmailTests(EmailTestBase):
    def send(self, **extra):
        body = {"producer_id": str(self.p1), "product_id": str(self.pub1), "user_name": "Maria Rossi",
                "user_email": "maria@esempio.it", "message": "Avete cartoni da 6?", "privacy_accepted": True}
        body.update(extra)
        return self.client.post(f"{API}/inquiries", json=body)

    def test_inquiry_notifies_winery_and_customer(self):
        run(self.db.producers.update_one({"_id": self.p1}, {"$set": {"contacts": {"email_contact": "vendite@uno.it"}}}))
        r = self.send()
        self.assertEqual(r.status_code, 200, r.text)
        to_winery = self.outbox("nuova_richiesta_cantina")[0]
        self.assertEqual(to_winery["to"], ["vendite@uno.it"])
        self.assertIn("Maria Rossi", to_winery["subject"])
        self.assertIn("Avete cartoni da 6?", to_winery["text"])
        self.assertIn("Tintilia Pubblicata", to_winery["text"])
        self.assertEqual(self.outbox("conferma_richiesta_cliente")[0]["to"], ["maria@esempio.it"])
        saved = run(self.db.inquiries.find_one({"user_email": "maria@esempio.it"}))
        self.assertIsNotNone(saved["privacy_accepted_at"])
        self.assertNotIn("privacy_accepted", saved)

    def test_winery_without_contact_email_uses_login_email(self):
        self.send()
        self.assertEqual(self.outbox("nuova_richiesta_cantina")[0]["to"], ["uno@test.it"])

    def test_inquiry_requires_privacy(self):
        r = self.send(privacy_accepted=False)
        self.assertEqual(r.status_code, 422)
        self.assertIn("privacy", r.json()["detail"])
        self.assertEqual(self.outbox(), [])

    def test_customer_text_is_escaped_in_html(self):
        self.send(user_name="<script>alert(1)</script>")
        self.assertNotIn("<script>", self.outbox("nuova_richiesta_cantina")[0]["html"])


class PasswordResetTests(EmailTestBase):
    def reset_token(self):
        html = self.outbox("recupero_password")[-1]["html"]
        return re.search(r"token=([A-Za-z0-9_\-]+)", html).group(1)

    def test_full_reset_flow(self):
        r = self.client.post(f"{API}/auth/password/forgot", json={"email": "UNO@test.it"})
        self.assertEqual(r.status_code, 200)
        token = self.reset_token()
        r = self.client.post(f"{API}/auth/password/reset", json={"token": token, "password": "NuovaPassword9"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(len(self.outbox("password_modificata")), 1)
        # la vecchia password non vale piu', la nuova si'
        self.assertEqual(self.client.post(f"{API}/auth/login", json={"email": "uno@test.it", "password": "Password123!"}).status_code, 400)
        login = self.client.post(f"{API}/auth/login", json={"email": "uno@test.it", "password": "NuovaPassword9"})
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.client.get(f"{API}/auth/me", headers=self.auth(login.json()["access_token"])).status_code, 200)
        # lo stesso link non si puo' riusare
        r = self.client.post(f"{API}/auth/password/reset", json={"token": token, "password": "AltraPassword9"})
        self.assertEqual(r.status_code, 400)

    def test_old_sessions_are_closed_after_reset(self):
        user = run(self.db.users.find_one({"email": "uno@test.it"}))
        run(self.db.users.update_one({"_id": user["_id"]}, {"$set": {"password_changed_at": datetime.utcnow() + timedelta(seconds=5)}}))
        self.assertEqual(self.client.get(f"{API}/auth/me", headers=self.auth(self.p1_token)).status_code, 401)

    def test_unknown_email_gets_same_answer_and_no_email(self):
        r = self.client.post(f"{API}/auth/password/forgot", json={"email": "nessuno@test.it"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("Se l'indirizzo è registrato", r.json()["message"])
        self.assertEqual(self.outbox("recupero_password"), [])

    def test_expired_link(self):
        self.client.post(f"{API}/auth/password/forgot", json={"email": "uno@test.it"})
        token = self.reset_token()
        run(self.db.password_resets.update_one({}, {"$set": {"expires_at": datetime.utcnow() - timedelta(minutes=1)}}))
        r = self.client.post(f"{API}/auth/password/reset", json={"token": token, "password": "NuovaPassword9"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("scaduto", r.json()["detail"])

    def test_at_most_three_links_per_hour(self):
        for _ in range(4):
            self.client.post(f"{API}/auth/password/forgot", json={"email": "uno@test.it"})
        self.assertEqual(len(self.outbox("recupero_password")), 3)


class DeletionRequestTests(EmailTestBase):
    def test_request_and_cancel(self):
        h = self.auth(self.p1_token)
        r = self.client.post(f"{API}/producers/me/deletion-request", json={"reason": "Chiudiamo l'attività"}, headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        email = self.outbox("richiesta_cancellazione_admin")[0]
        self.assertEqual(email["to"], ["admin@test.it"])
        self.assertIn("Chiudiamo l'attività", email["text"])
        me = self.client.get(f"{API}/auth/me", headers=h).json()
        self.assertIsNotNone(me["producer"]["deletion_requested_at"])
        # i visitatori non vedono la richiesta
        public = self.client.get(f"{API}/producers/cantina-uno").json()
        self.assertIsNone(public.get("deletion_requested_at"))
        # l'admin la vede nell'elenco completo
        listing = self.client.get(f"{API}/producers?include_all=true", headers=self.auth(self.admin_token)).json()
        self.assertTrue(next(p for p in listing if p["slug"] == "cantina-uno")["deletion_requested_at"])
        self.assertEqual(self.client.delete(f"{API}/producers/me/deletion-request", headers=h).status_code, 200)
        self.assertNotIn("deletion_requested_at", run(self.db.producers.find_one({"_id": self.p1})))

    def test_producer_still_cannot_delete_directly(self):
        r = self.client.delete(f"{API}/producers/{self.p1}", headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 403)


class EmailAdminTests(EmailTestBase):
    def test_templates_crud_preview_and_test(self):
        h = self.auth(self.admin_token)
        templates = self.client.get(f"{API}/emails/templates", headers=h).json()
        self.assertEqual({t["key"] for t in templates}, set(mail.DEFAULT_TEMPLATES))
        r = self.client.put(f"{API}/emails/templates/cantina_approvata",
                            json={"subject": "Evviva {{nome_cantina}}!", "body": "Siete online.\n\n[[Vai|{{link_sito}}]]"}, headers=h)
        self.assertTrue(r.json()["customized"])
        preview = self.client.post(f"{API}/emails/templates/cantina_approvata/preview",
                                   json={"subject": "Evviva {{nome_cantina}}!", "body": "Ciao\n\n[[Vai|{{link_sito}}]]"}, headers=h).json()
        self.assertEqual(preview["subject"], "Evviva Cantina Colle dei Venti!")
        self.assertIn('href="' + settings.SITE_URL + '/"', preview["html"])
        # l'approvazione usa il testo personalizzato
        self.client.put(f"{API}/producers/{self.p_pending}", json={"status": "APPROVED"}, headers=h)
        self.assertEqual(self.outbox("cantina_approvata")[0]["subject"], "Evviva Cantina Attesa!")
        # prova e ripristino
        test = self.client.post(f"{API}/emails/templates/cantina_approvata/test", json={}, headers=h).json()
        self.assertEqual(test["to"], ["admin@test.it"])
        reset = self.client.post(f"{API}/emails/templates/cantina_approvata/reset", headers=h).json()
        self.assertFalse(reset["customized"])
        self.assertIn("è online", reset["subject"])

    def test_outbox_and_settings(self):
        h = self.auth(self.admin_token)
        register(self.client)
        items = self.client.get(f"{API}/emails/outbox", headers=h).json()
        self.assertEqual(len(items), 2)
        self.assertNotIn("html", items[0])
        detail = self.client.get(f"{API}/emails/outbox/{items[0]['id']}", headers=h).json()
        self.assertIn("<html", detail["html"])
        status = self.client.get(f"{API}/emails/status", headers=h).json()
        self.assertEqual(status["mode"], "outbox")
        r = self.client.put(f"{API}/emails/settings", json={"sender_name": "Enoteca", "admin_recipients": ["A@B.it"]}, headers=h)
        self.assertEqual(r.json()["effective_admin_recipients"], ["a@b.it"])
        self.assertEqual(self.client.delete(f"{API}/emails/outbox", headers=h).json()["deleted"], 2)

    def test_email_admin_is_admin_only(self):
        h = self.auth(self.p1_token)
        for method, path in [("get", "templates"), ("get", "outbox"), ("get", "settings"), ("get", "status")]:
            self.assertEqual(getattr(self.client, method)(f"{API}/emails/{path}", headers=h).status_code, 403)

    def test_smtp_mode_without_host_falls_back_to_outbox(self):
        saved = settings.EMAIL_MODE
        settings.EMAIL_MODE = "smtp"
        try:
            self.assertEqual(mail.email_mode(), "outbox")
        finally:
            settings.EMAIL_MODE = saved


class SitePagesTests(BaseTest):
    def test_privacy_page_default_and_edit(self):
        r = self.client.get(f"{API}/site/pages/privacy")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Titolare del trattamento", r.json()["body"])
        self.assertEqual(self.client.put(f"{API}/site/pages/privacy", json={"body": "x"}, headers=self.auth(self.p1_token)).status_code, 403)
        r = self.client.put(f"{API}/site/pages/privacy", json={"body": "Nuovo testo"}, headers=self.auth(self.admin_token))
        self.assertEqual(self.client.get(f"{API}/site/pages/privacy").json()["body"], "Nuovo testo")
        self.client.post(f"{API}/site/pages/privacy/reset", headers=self.auth(self.admin_token))
        self.assertIn("Titolare", self.client.get(f"{API}/site/pages/privacy").json()["body"])
        self.assertEqual(self.client.get(f"{API}/site/pages/inesistente").status_code, 404)

    def test_about_page_exists(self):
        r = self.client.get(f"{API}/site/pages/chi-siamo")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["title"], "Chi siamo")

    def test_cookie_page_lists_the_site_cookies(self):
        r = self.client.get(f"{API}/site/pages/cookie")
        self.assertEqual(r.status_code, 200)
        body = r.json()["body"]
        # i nomi devono restare allineati a useAuth e useCookieConsent del frontend
        self.assertIn("auth_token", body)
        self.assertIn("em_consenso_cookie", body)
        r = self.client.put(f"{API}/site/pages/cookie", json={"title": "Cookie"}, headers=self.auth(self.admin_token))
        self.assertEqual(r.json()["title"], "Cookie")


class CatalogRulesTests(BaseTest):
    def setUp(self):
        super().setUp()
        for name in ["Antipasti", "Formaggi Stagionati"]:
            run(self.db.pairings.insert_one({"name": name}))

    def test_producer_free_pairings_go_to_attribute(self):
        r = self.client.post(f"{API}/products", json={
            "name": "Vino Libero", "category": "VINO_ROSSO", "food_pairings": ["antipasti", "Agnello alla brace", "Pampanella"],
        }, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body["food_pairings"], ["Antipasti"])
        attr = next(a for a in body["custom_attributes"] if a["name"] == "Abbinamenti Consigliati")
        self.assertEqual(attr["value"], "Agnello alla brace, Pampanella")
        # l'elenco ufficiale non si allarga
        self.assertEqual(run(self.db.pairings.count_documents({})), 2)
        # anche in modifica
        r = self.client.put(f"{API}/products/{body['id']}", json={"food_pairings": ["Formaggi stagionati", "Zuppa di fave"]},
                            headers=self.auth(self.p1_token)).json()
        self.assertEqual(r["food_pairings"], ["Formaggi Stagionati"])
        attr = next(a for a in r["custom_attributes"] if a["name"] == "Abbinamenti Consigliati")
        self.assertIn("Zuppa di fave", attr["value"])

    def test_admin_can_still_extend_the_list(self):
        self.client.post(f"{API}/products", json={"name": "Vino Admin", "producer_id": str(self.p1), "category": "VINO_ROSSO",
                                                  "food_pairings": ["Agnello alla brace"]}, headers=self.auth(self.admin_token))
        self.assertEqual(run(self.db.pairings.count_documents({"name": "Agnello alla brace"})), 1)

    def test_merge_attributes(self):
        a = run(self.db.attributes.insert_one({"name": "Filtrazioni", "suggested_values": ["Sterile"]})).inserted_id
        b = run(self.db.attributes.insert_one({"name": "Filtrazione", "suggested_values": ["Leggera"]})).inserted_id
        run(self.db.products.update_one({"_id": self.pub1}, {"$set": {"custom_attributes": [{"name": "Filtrazioni", "value": "Sterile"}]}}))
        r = self.client.post(f"{API}/attributes/{a}/merge", json={"target_id": str(b)}, headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["products_updated"], 1)
        self.assertIsNone(run(self.db.attributes.find_one({"_id": a})))
        self.assertEqual(run(self.db.attributes.find_one({"_id": b}))["suggested_values"], ["Leggera", "Sterile"])
        self.assertEqual(run(self.db.products.find_one({"_id": self.pub1}))["custom_attributes"], [{"name": "Filtrazione", "value": "Sterile"}])
        self.assertEqual(self.client.post(f"{API}/attributes/{b}/merge", json={"target_id": str(b)},
                                          headers=self.auth(self.admin_token)).status_code, 400)
        self.assertEqual(self.client.post(f"{API}/grapes/{b}/merge", json={"target_id": str(a)},
                                          headers=self.auth(self.p1_token)).status_code, 403)


class InquiryDeleteTests(EmailTestBase):
    def _inquiry(self, producer_id):
        return run(self.db.inquiries.insert_one({"producer_id": producer_id, "user_name": "Mario", "user_email": "m@example.com",
                                                 "message": "Ciao", "message_type": "ALTRO", "is_read": False,
                                                 "created_at": datetime.utcnow()})).inserted_id

    def test_winery_deletes_only_its_own_messages(self):
        mine, other = self._inquiry(self.p1), self._inquiry(self.p2)
        self.assertEqual(self.client.delete(f"{API}/inquiries/{other}", headers=self.auth(self.p1_token)).status_code, 403)
        self.assertEqual(self.client.delete(f"{API}/inquiries/{mine}", headers=self.auth(self.p1_token)).status_code, 200)
        self.assertIsNone(run(self.db.inquiries.find_one({"_id": mine})))
        self.assertIsNotNone(run(self.db.inquiries.find_one({"_id": other})))

    def test_admin_deletes_any_message(self):
        territory = self._inquiry(None)
        self.assertEqual(self.client.delete(f"{API}/inquiries/{territory}", headers=self.auth(self.p1_token)).status_code, 403)
        self.assertEqual(self.client.delete(f"{API}/inquiries/{territory}", headers=self.auth(self.admin_token)).status_code, 200)
        self.assertEqual(self.client.delete(f"{API}/inquiries/{territory}", headers=self.auth(self.admin_token)).status_code, 404)


class InviteTests(EmailTestBase):
    def setUp(self):
        super().setUp()
        run(self.db.producers.update_one({"_id": self.p2}, {"$set": {"contacts": {"email_contact": "Info@CantinaDue.it"}}}))
        # Cantina Due e' stata inserita dall'amministratore: nessun account
        run(self.db.users.delete_many({"producer_id": self.p2}))

    def invite(self, pid, **body):
        return self.client.post(f"{API}/producers/{pid}/invite", json=body, headers=self.auth(self.admin_token))

    def token_from_mail(self):
        mail_doc = self.outbox("invito_cantina")[-1]
        return re.search(r"attiva-account\?token=([\w-]+)", mail_doc["text"]).group(1)

    def account(self, pid):
        ps = self.client.get(f"{API}/producers?include_all=true", headers=self.auth(self.admin_token)).json()
        return next(p for p in ps if p["id"] == str(pid))["account"]

    def test_full_invite_flow(self):
        self.assertEqual(self.account(self.p2)["status"], "none")
        r = self.invite(self.p2)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["email"], "info@cantinadue.it")
        self.assertEqual(self.outbox("invito_cantina")[0]["to"], ["info@cantinadue.it"])
        self.assertEqual(self.account(self.p2)["status"], "invited")
        token = self.token_from_mail()
        # finche' non sceglie la password non si entra
        r = self.client.post(f"{API}/auth/login", json={"email": "info@cantinadue.it", "password": "qualsiasi"})
        self.assertEqual(r.status_code, 400)
        info = self.client.get(f"{API}/auth/invite/{token}").json()
        self.assertEqual(info["company_name"], "Cantina Due")
        # privacy obbligatoria
        r = self.client.post(f"{API}/auth/invite/accept", json={"token": token, "password": "Vigneto2026!"})
        self.assertEqual(r.status_code, 422)
        r = self.client.post(f"{API}/auth/invite/accept", json={"token": token, "password": "Vigneto2026!", "privacy_accepted": True})
        self.assertEqual(r.status_code, 200, r.text)
        me = self.client.get(f"{API}/auth/me", headers=self.auth(r.json()["access_token"])).json()
        self.assertEqual(me["producer_id"], str(self.p2))
        self.assertEqual(self.account(self.p2)["status"], "active")
        # il link vale una volta sola e non si reinvita una cantina gia' attiva
        self.assertEqual(self.client.post(f"{API}/auth/invite/accept", json={"token": token, "password": "Altra2026!", "privacy_accepted": True}).status_code, 400)
        self.assertEqual(self.invite(self.p2).status_code, 400)
        self.assertEqual(self.client.post(f"{API}/auth/login", json={"email": "info@cantinadue.it", "password": "Vigneto2026!"}).status_code, 200)

    def test_resend_replaces_previous_link(self):
        self.invite(self.p2)
        first = self.token_from_mail()
        self.invite(self.p2)
        second = self.token_from_mail()
        self.assertEqual(self.client.get(f"{API}/auth/invite/{first}").status_code, 400)
        self.assertEqual(self.client.get(f"{API}/auth/invite/{second}").status_code, 200)
        self.assertEqual(run(self.db.users.count_documents({"producer_id": self.p2})), 1)

    def test_expired_invite(self):
        self.invite(self.p2)
        token = self.token_from_mail()
        run(self.db.password_resets.update_many({}, {"$set": {"expires_at": datetime.utcnow() - timedelta(days=1)}}))
        run(self.db.users.update_many({"producer_id": self.p2}, {"$set": {"invite_expires_at": datetime.utcnow() - timedelta(days=1)}}))
        self.assertEqual(self.client.get(f"{API}/auth/invite/{token}").status_code, 400)
        self.assertEqual(self.account(self.p2)["status"], "expired")

    def test_rules(self):
        # cantina registrata da sola: ha gia' l'accesso
        self.assertEqual(self.invite(self.p1).status_code, 400)
        # email gia' usata da un altro account
        self.assertEqual(self.invite(self.p2, email="uno@test.it").status_code, 400)
        # senza email
        run(self.db.producers.update_one({"_id": self.p2}, {"$set": {"contacts": {}}}))
        self.assertIn("manca l'email", self.invite(self.p2).json()["detail"])
        # solo l'amministratore
        r = self.client.post(f"{API}/producers/{self.p2}/invite", json={}, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.account(self.p1)["status"], "active")

    def test_invite_all(self):
        p3 = self._producer("Cantina Tre", "cantina-tre")
        run(self.db.producers.update_one({"_id": p3}, {"$set": {"contacts": {"email_contact": "tre@example.com"}}}))
        r = self.client.post(f"{API}/producers/invite-all", headers=self.auth(self.admin_token)).json()
        names = sorted(i["company_name"] for i in r["invited"])
        self.assertEqual(names, ["Cantina Due", "Cantina Tre"])
        # la cantina in attesa con account e Cantina Uno (attiva) non vengono toccate
        self.assertEqual(len(self.outbox("invito_cantina")), 2)
        again = self.client.post(f"{API}/producers/invite-all", headers=self.auth(self.admin_token)).json()
        self.assertEqual(again["invited"], [])
