"""Test di sicurezza e regressione del backend.

Eseguire dalla cartella backend/:
    pip install -r requirements-dev.txt
    python -m pytest -q          (oppure: python -m unittest discover -s tests)
"""
import asyncio
import io
import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SECRET_KEY", "test-secret-key-" + "x" * 48)

from bson import ObjectId  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from tests.fake_mongo import FakeClient  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.security import create_access_token, get_password_hash  # noqa: E402
from app.core.utils import rate_limiter  # noqa: E402
from app.db import mongodb  # noqa: E402
import main  # noqa: E402

API = "/api/v1"


def run(coro):
    return asyncio.run(coro)


class BaseTest(unittest.TestCase):
    def setUp(self):
        mongodb.db.client = FakeClient()
        self.db = mongodb.db.client[settings.DATABASE_NAME]
        rate_limiter.clear()
        run(main.ensure_indexes(self.db))
        self.client = TestClient(main.app)

        self.p1 = self._producer("Cantina Uno", "cantina-uno")
        self.p2 = self._producer("Cantina Due", "cantina-due")
        self.p_pending = self._producer("Cantina Attesa", "cantina-attesa", status="PENDING_APPROVAL")

        self.admin_token = self._user("admin@test.it", "ADMIN")
        self.p1_token = self._user("uno@test.it", "PRODUCER", self.p1)
        self.p2_token = self._user("due@test.it", "PRODUCER", self.p2)
        self.pending_token = self._user("attesa@test.it", "PRODUCER", self.p_pending)

        self.pub1 = self._product("Tintilia Pubblicata", "tintilia-pubblicata", self.p1)
        self.draft1 = self._product("Tintilia Bozza", "tintilia-bozza", self.p1, status="DRAFT")
        self.pub2 = self._product("Biferno Rosso", "biferno-rosso", self.p2)
        self.pub_pending = self._product("Vino Cantina In Attesa", "vino-attesa", self.p_pending)

    # --- helper -------------------------------------------------------------
    def _producer(self, name, slug, status="APPROVED"):
        res = run(self.db.producers.insert_one({
            "company_name": name, "slug": slug, "status": status,
            "address": {"city": "Campobasso", "province": "CB"}, "contacts": {},
            "created_at": datetime.utcnow(),
        }))
        return res.inserted_id

    def _user(self, email, role, producer_id=None):
        res = run(self.db.users.insert_one({
            "email": email, "password_hash": get_password_hash("Password123!"), "role": role,
            "producer_id": producer_id, "is_active": True, "created_at": datetime.utcnow(),
        }))
        return create_access_token(str(res.inserted_id), role, str(producer_id) if producer_id else None)

    def _product(self, name, slug, producer_id, status="PUBLISHED"):
        res = run(self.db.products.insert_one({
            "name": name, "slug": slug, "producer_id": producer_id, "status": status,
            "category": "VINO_ROSSO", "denominazione": "DOC", "grape_varieties": [], "food_pairings": [],
            "custom_attributes": [], "photos": [], "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
        }))
        return res.inserted_id

    @staticmethod
    def auth(token):
        return {"Authorization": f"Bearer {token}"}


class AuthTests(BaseTest):
    def test_register_cannot_choose_admin_role(self):
        r = self.client.post(f"{API}/auth/register", json={
            "email": "hacker@test.it", "password": "Password123!", "role": "ADMIN", "company_name": "Hack"
        })
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["role"], "PRODUCER")
        user = run(self.db.users.find_one({"email": "hacker@test.it"}))
        self.assertEqual(user["role"], "PRODUCER")
        producer = run(self.db.producers.find_one({"_id": user["producer_id"]}))
        self.assertEqual(producer["status"], "PENDING_APPROVAL")

    def test_register_rejects_short_password(self):
        r = self.client.post(f"{API}/auth/register", json={"email": "a@test.it", "password": "123"})
        self.assertEqual(r.status_code, 422)

    def test_register_duplicate_company_gets_unique_slug(self):
        for i in range(2):
            r = self.client.post(f"{API}/auth/register", json={
                "email": f"dup{i}@test.it", "password": "Password123!", "company_name": "Cantina Uno"
            })
            self.assertEqual(r.status_code, 200, r.text)
        slugs = [d["slug"] for d in self.db.producers.docs]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_login_rate_limited(self):
        for _ in range(settings.LOGIN_MAX_ATTEMPTS):
            r = self.client.post(f"{API}/auth/login", json={"email": "uno@test.it", "password": "sbagliata"})
            self.assertEqual(r.status_code, 400)
        r = self.client.post(f"{API}/auth/login", json={"email": "uno@test.it", "password": "Password123!"})
        self.assertEqual(r.status_code, 429)

    def test_login_ok_and_inactive_user_blocked(self):
        r = self.client.post(f"{API}/auth/login", json={"email": "uno@test.it", "password": "Password123!"})
        self.assertEqual(r.status_code, 200)
        token = r.json()["access_token"]
        run(self.db.users.update_one({"email": "uno@test.it"}, {"$set": {"is_active": False}}))
        self.assertEqual(self.client.get(f"{API}/auth/me", headers=self.auth(token)).status_code, 401)

    def test_forged_token_rejected(self):
        from jose import jwt
        forged = jwt.encode({"sub": str(ObjectId()), "role": "ADMIN"}, "enotecamolise_secret_jwt_key_2026_super_secure_key", "HS256")
        r = self.client.get(f"{API}/admin/stats", headers=self.auth(forged))
        self.assertEqual(r.status_code, 401)


class ProductVisibilityTests(BaseTest):
    def _names(self, r):
        self.assertEqual(r.status_code, 200, r.text)
        return {p["name"] for p in r.json()}

    def test_public_list_hides_drafts_and_unapproved(self):
        names = self._names(self.client.get(f"{API}/products"))
        self.assertIn("Tintilia Pubblicata", names)
        self.assertNotIn("Tintilia Bozza", names)
        self.assertNotIn("Vino Cantina In Attesa", names)

    def test_status_all_requires_auth(self):
        self.assertEqual(self.client.get(f"{API}/products?status=ALL").status_code, 401)

    def test_producer_sees_only_own_drafts(self):
        names = self._names(self.client.get(f"{API}/products?status=ALL", headers=self.auth(self.p1_token)))
        self.assertEqual(names, {"Tintilia Pubblicata", "Tintilia Bozza"})
        r = self.client.get(f"{API}/products?status=ALL&producer_id={self.p2}", headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 403)

    def test_admin_sees_everything(self):
        names = self._names(self.client.get(f"{API}/products?status=ALL", headers=self.auth(self.admin_token)))
        self.assertEqual(len(names), 4)

    def test_draft_detail_only_for_owner_or_admin(self):
        self.assertEqual(self.client.get(f"{API}/products/tintilia-bozza").status_code, 404)
        self.assertEqual(self.client.get(f"{API}/products/tintilia-bozza", headers=self.auth(self.p2_token)).status_code, 404)
        self.assertEqual(self.client.get(f"{API}/products/tintilia-bozza", headers=self.auth(self.p1_token)).status_code, 200)
        self.assertEqual(self.client.get(f"{API}/products/tintilia-bozza", headers=self.auth(self.admin_token)).status_code, 200)
        self.assertEqual(self.client.get(f"{API}/products/tintilia-pubblicata").status_code, 200)

    def test_report_excludes_drafts(self):
        run(self.db.products.delete_many({"status": "PUBLISHED"}))
        r = self.client.get(f"{API}/reports/summary")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertNotIn("Tintilia Bozza", r.text)

    def test_manual_duplicate_slug_does_not_crash(self):
        body = {"name": "Nuovo Vino", "slug": "tintilia-pubblicata", "producer_id": str(self.p1)}
        r = self.client.post(f"{API}/products", json=body, headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertNotEqual(r.json()["slug"], "tintilia-pubblicata")

    def test_invalid_status_rejected(self):
        body = {"name": "Vino X", "status": "HACKED"}
        r = self.client.post(f"{API}/products", json=body, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 422)

    def test_clone_to_other_producer_assigns_it(self):
        r = self.client.post(f"{API}/products/{self.pub1}/clone?target_producer_id={self.p2}", headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["producer_id"], str(self.p2))

    def test_producer_cannot_edit_other_wine(self):
        r = self.client.put(f"{API}/products/{self.pub2}", json={"name": "X"}, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 403)


class BatchImportTests(BaseTest):
    wines = [{"name": "Vino PDF", "grape_varieties": ["Tintilia"]}]

    def test_pdf_import_is_admin_only(self):
        r = self.client.post(f"{API}/products/import/confirm-batch",
                             json={"producer_id": str(self.p1), "wines": self.wines}, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 403)
        r = self.client.post(f"{API}/products/import/parse-pdfs",
                             files={"files": ("a.pdf", b"%PDF-1.4", "application/pdf")}, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.client.get(f"{API}/products/import/ai-status", headers=self.auth(self.p1_token)).status_code, 403)
        self.assertEqual(run(self.db.products.count_documents({"name": "Vino PDF"})), 0)

    def test_wine_fields_are_sanitized(self):
        r = self.client.post(f"{API}/products/import/confirm-batch",
                             json={"producer_id": str(self.p2), "wines": [{"name": "Ok 2021 DOC", "alcohol_degrees": "abc", "status": "HACK"}]},
                             headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200, r.text)
        doc = run(self.db.products.find_one({"producer_id": self.p2, "name": "Ok"}))
        self.assertIsNotNone(doc)
        self.assertIsNone(doc["alcohol_degrees"])
        self.assertEqual(doc["status"], "PUBLISHED")

    def test_non_object_rows_rejected(self):
        r = self.client.post(f"{API}/products/import/confirm-batch",
                             json={"producer_id": str(self.p2), "wines": ["x"]}, headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 422)


class UploadTests(BaseTest):
    def setUp(self):
        super().setUp()
        import tempfile
        self._tmp = tempfile.mkdtemp()
        self._old_dir = settings.UPLOAD_DIR
        settings.UPLOAD_DIR = self._tmp

    def tearDown(self):
        settings.UPLOAD_DIR = self._old_dir

    def test_svg_rejected(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        r = self.client.post(f"{API}/uploads/image", files={"file": ("x.svg", svg, "image/svg+xml")}, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 400)

    def test_fake_image_rejected(self):
        r = self.client.post(f"{API}/uploads/image", files={"file": ("x.png", b"<html><script>1</script>", "image/png")}, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 400)

    def test_real_image_converted_to_webp(self):
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (10, 10), "red").save(buf, "PNG")
        r = self.client.post(f"{API}/uploads/image", files={"file": ("x.png", buf.getvalue(), "image/png")}, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["url"].endswith(".webp"))

    def test_fake_pdf_rejected(self):
        r = self.client.post(f"{API}/uploads/document", files={"file": ("x.pdf", b"not a pdf", "application/pdf")}, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 400)

    def test_upload_requires_auth(self):
        r = self.client.post(f"{API}/uploads/image", files={"file": ("x.png", b"x", "image/png")})
        self.assertEqual(r.status_code, 401)


class ProducerTests(BaseTest):
    def test_producer_cannot_self_approve(self):
        r = self.client.put(f"{API}/producers/{self.p_pending}", json={"status": "APPROVED"}, headers=self.auth(self.pending_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["status"], "PENDING_APPROVAL")

    def test_admin_can_approve(self):
        r = self.client.put(f"{API}/producers/{self.p_pending}", json={"status": "APPROVED"}, headers=self.auth(self.admin_token))
        self.assertEqual(r.json()["status"], "APPROVED")

    def test_rename_to_existing_name_gets_unique_slug(self):
        r = self.client.put(f"{API}/producers/{self.p2}", json={"company_name": "Cantina Uno"}, headers=self.auth(self.p2_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertNotEqual(r.json()["slug"], "cantina-uno")

    def test_pending_producer_hidden_from_public(self):
        self.assertEqual(self.client.get(f"{API}/producers/cantina-attesa").status_code, 404)
        self.assertEqual(self.client.get(f"{API}/producers/cantina-attesa", headers=self.auth(self.pending_token)).status_code, 200)
        names = {p["company_name"] for p in self.client.get(f"{API}/producers").json()}
        self.assertNotIn("Cantina Attesa", names)

    def test_include_all_admin_only(self):
        self.assertEqual(self.client.get(f"{API}/producers?include_all=true", headers=self.auth(self.p1_token)).status_code, 403)
        r = self.client.get(f"{API}/producers?include_all=true", headers=self.auth(self.admin_token))
        self.assertEqual(len(r.json()), 3)

    def test_producer_cannot_edit_other_producer(self):
        r = self.client.put(f"{API}/producers/{self.p2}", json={"description": "x"}, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 403)


class TaxonomyTests(BaseTest):
    def test_producer_cannot_rename_shared_taxonomy(self):
        for coll, path in (("attributes", "attributes"), ("grapes", "grapes"), ("pairings", "pairings")):
            oid = run(self.db[coll].insert_one({"name": "Voce", "created_at": datetime.utcnow()})).inserted_id
            r = self.client.put(f"{API}/{path}/{oid}", json={"name": "Vandalizzato"}, headers=self.auth(self.p1_token))
            self.assertEqual(r.status_code, 403, path)


class InquiryTests(BaseTest):
    def _send(self, producer_id):
        return self.client.post(f"{API}/inquiries", json={
            "producer_id": str(producer_id), "user_name": "Mario", "user_email": "mario@test.it", "message": "Ciao"
        })

    def test_inquiry_rate_limited(self):
        for _ in range(settings.INQUIRY_MAX_PER_WINDOW):
            self.assertEqual(self._send(self.p1).status_code, 200)
        self.assertEqual(self._send(self.p1).status_code, 429)

    def test_inquiry_to_unapproved_producer_rejected(self):
        self.assertEqual(self._send(self.p_pending).status_code, 404)

    def test_producer_reads_only_own_inquiries(self):
        self._send(self.p1)
        self._send(self.p2)
        r = self.client.get(f"{API}/inquiries", headers=self.auth(self.p1_token))
        self.assertEqual({i["producer_id"] for i in r.json()}, {str(self.p1)})


class StartupTests(BaseTest):
    def test_sample_seed_works_on_empty_db(self):
        mongodb.db.client = FakeClient()
        db = mongodb.db.client[settings.DATABASE_NAME]
        old = settings.SEED_SAMPLE_DATA
        settings.SEED_SAMPLE_DATA = True
        try:
            run(main.seed_sample_data(db))
        finally:
            settings.SEED_SAMPLE_DATA = old
        self.assertEqual(run(db.products.count_documents({})), 2)
        self.assertEqual(run(db.users.count_documents({})), 0)

    def test_no_admin_created_without_password(self):
        mongodb.db.client = FakeClient()
        db = mongodb.db.client[settings.DATABASE_NAME]
        old = settings.ADMIN_PASSWORD
        settings.ADMIN_PASSWORD = None
        try:
            run(main.ensure_admin_user(db))
        finally:
            settings.ADMIN_PASSWORD = old
        self.assertEqual(run(db.users.count_documents({})), 0)

    def test_cors_rejects_unknown_origin(self):
        r = self.client.get("/", headers={"Origin": "https://evil.example"})
        self.assertNotIn("access-control-allow-origin", {k.lower() for k in r.headers})
        r = self.client.get("/", headers={"Origin": "http://localhost:3000"})
        self.assertEqual(r.headers.get("access-control-allow-origin"), "http://localhost:3000")


if __name__ == "__main__":
    unittest.main()
