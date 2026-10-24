"""Protezioni aggiunte dopo la verifica di sicurezza di ottobre 2026."""
from datetime import datetime

from tests.test_security import API, BaseTest, run
from app.core.config import settings
from app.core.utils import rate_limiter
import main


class ClientIpTests(BaseTest):
    URL = f"{API}/auth/invite/token-inventato-per-la-prova-xyz"

    def hit(self, xff):
        return self.client.get(self.URL, headers={"X-Forwarded-For": xff}).status_code

    def test_spoofed_forwarded_for_does_not_bypass_limits(self):
        # Google aggiunge l'IP vero in fondo: i valori all'inizio li sceglie chi chiama
        codes = [self.hit(f"80.17.4.{i}, 93.40.12.7") for i in range(35)]
        self.assertEqual(codes[:30], [400] * 30)
        self.assertIn(429, codes[30:])

    def test_different_real_ips_have_separate_limits(self):
        for i in range(30):
            self.hit("93.40.12.7")
        self.assertEqual(self.hit("93.40.12.7"), 429)
        self.assertEqual(self.hit("93.40.12.8"), 400)

    def test_google_balancer_and_private_hops_are_skipped(self):
        for i in range(30):
            self.hit(f"80.17.4.{i}, 93.40.12.9, 35.191.4.5")
        self.assertEqual(self.hit("1.1.1.1, 93.40.12.9, 130.211.0.1, 10.0.0.2"), 429)


class LoginLockoutTests(BaseTest):
    def login(self, password, ip):
        return self.client.post(f"{API}/auth/login", json={"email": "admin@test.it", "password": password},
                                headers={"X-Forwarded-For": ip}).status_code

    def test_account_lockout_holds_across_ips_and_restarts(self):
        for i in range(settings.LOGIN_ACCOUNT_MAX_FAILURES):
            self.assertEqual(self.login("sbagliata", f"93.40.12.{i}"), 400)
        rate_limiter.clear()  # come un riavvio di Cloud Run: il limite in memoria si azzera
        self.assertEqual(self.login("Password123!", "93.40.12.250"), 429)
        self.assertEqual(run(self.db.login_failures.count_documents({"email": "admin@test.it"})),
                         settings.LOGIN_ACCOUNT_MAX_FAILURES)

    def test_successful_login_clears_failures(self):
        for i in range(3):
            self.login("sbagliata", "93.40.12.1")
        self.assertEqual(self.login("Password123!", "93.40.12.2"), 200)
        self.assertEqual(run(self.db.login_failures.count_documents({})), 0)


class DocsTests(BaseTest):
    def test_api_docs_off_by_default(self):
        self.assertFalse(settings.API_DOCS)
        for path in ("/docs", "/redoc", f"{API}/openapi.json"):
            self.assertEqual(self.client.get(path).status_code, 404, path)
