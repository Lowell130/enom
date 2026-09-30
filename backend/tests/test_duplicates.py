"""Riconoscimento dei vini doppi durante l'importazione delle schede."""
import copy
import unittest
from unittest import mock

from tests.test_security import API, BaseTest, run
from tests.test_pdf_import import AIConfigMixin, CATABBO_AI, CATABBO_PDF, gemini_reply, FakeResponse
from app.core.config import settings
from app.services import ai_extractor
from app.services.duplicates import compare_names, find_duplicate


class CompareNamesTests(unittest.TestCase):
    CASES = [
        ("Colle del Limone – Falanghina del Molise", "Colle del Limone", "similar"),
        ("Colle del Limone – Falanghina del Molise", "colle del limone - falanghina del molise DOP 2022", "exact"),
        ("Tintilia Molise", "Tintilia del Molise D.O.C.", "exact"),
        ("Tintilia del Molise Purezza", "Tintilia del Molise Purezzza", "similar"),
        ("Purezza", "Tintilia del Molise Purezza", "similar"),
        # vini diversi della stessa cantina: non sono doppioni
        ("Tintilia del Molise", "Tintilia del Molise Riserva", None),
        ("Biferno Rosso", "Biferno Rosato", None),
        ("I Diecettari – Molise Rosso", "Molise Rosso", None),
        ("Tintilia", "Tintilia 66", None),
        ("Tintilia del Molise Uno", "Tintilia del Molise Due", None),
        ("Falanghina", "Colle del Limone – Falanghina del Molise", None),
    ]

    def test_cases(self):
        for a, b, expected in self.CASES:
            with self.subTest(a=a, b=b):
                self.assertEqual(compare_names(a, b)[0], expected)

    def test_find_duplicate_respects_riserva_and_category(self):
        candidates = [{"_id": 1, "name": "Colle del Limone", "category": "VINO_BIANCO", "is_riserva": False}]
        self.assertEqual(find_duplicate("Colle del Limone – Falanghina", candidates, "VINO_BIANCO", False)["match"], "similar")
        self.assertIsNone(find_duplicate("Colle del Limone – Falanghina", candidates, "VINO_ROSSO", False))
        self.assertIsNone(find_duplicate("Colle del Limone", candidates, "VINO_BIANCO", True))


class DuplicateImportTests(AIConfigMixin, BaseTest):
    def setUp(self):
        super().setUp()
        settings.GEMINI_API_KEY = "k"

    def parse_many(self, files):
        return self.client.post(f"{API}/products/import/parse-pdfs",
                                files=[("files", (n, b, "application/pdf")) for n, b in files],
                                headers=self.auth(self.admin_token)).json()

    def test_similar_name_in_catalog_is_proposed_for_update(self):
        pid = run(self.db.products.insert_one({"name": "Colle del Limone", "slug": "colle-del-limone", "category": "VINO_BIANCO",
                                               "producer_id": self.catabbo, "status": "PUBLISHED"})).inserted_id
        with mock.patch.object(ai_extractor.requests, "post", return_value=gemini_reply(CATABBO_AI)):
            w = self.parse_many([("a.pdf", CATABBO_PDF)])["files"][0]["wines"][0]
        self.assertEqual(w["existing_product"]["id"], str(pid))
        self.assertEqual(w["existing_product"]["match"], "similar")
        self.assertEqual(w["action"], "update")

    def test_riserva_in_catalog_is_not_a_duplicate(self):
        run(self.db.products.insert_one({"name": "Colle del Limone – Falanghina del Molise Riserva", "is_riserva": True,
                                         "producer_id": self.catabbo, "status": "PUBLISHED", "slug": "x"}))
        with mock.patch.object(ai_extractor.requests, "post", return_value=gemini_reply(CATABBO_AI)):
            w = self.parse_many([("a.pdf", CATABBO_PDF)])["files"][0]["wines"][0]
        self.assertIsNone(w["existing_product"])
        self.assertEqual(w["action"], "create")

    def test_identical_file_analyzed_once(self):
        with mock.patch.object(ai_extractor.requests, "post", return_value=gemini_reply(CATABBO_AI)) as post:
            res = self.parse_many([("a.pdf", CATABBO_PDF), ("copia di a.pdf", CATABBO_PDF)])
        self.assertEqual(post.call_count, 1)
        self.assertEqual(res["files"][1]["status"], "duplicate")
        self.assertIn("a.pdf", res["files"][1]["error"])
        self.assertEqual(res["count"], 1)

    def test_same_wine_in_two_files_marked_in_batch(self):
        other = CATABBO_PDF + b"\n%altra versione"
        with mock.patch.object(ai_extractor.requests, "post", return_value=gemini_reply(CATABBO_AI)):
            res = self.parse_many([("scheda.pdf", CATABBO_PDF), ("pagina-web.pdf", other)])
        first, second = res["files"][0]["wines"][0], res["files"][1]["wines"][0]
        self.assertEqual(first["action"], "create")
        self.assertIsNone(first["batch_duplicate_of"])
        self.assertEqual(second["action"], "skip")
        self.assertEqual(second["batch_duplicate_of"]["source_file"], "scheda.pdf")

    def test_check_duplicate_endpoint(self):
        run(self.db.products.insert_one({"name": "Colle del Limone", "producer_id": self.p1, "status": "DRAFT", "slug": "c"}))
        r = self.client.post(f"{API}/products/import/check-duplicate",
                             json={"producer_id": str(self.p1), "name": "Colle del Limone – Falanghina del Molise"},
                             headers=self.auth(self.admin_token))
        self.assertEqual(r.json()["existing_product"]["name"], "Colle del Limone")
        r = self.client.post(f"{API}/products/import/check-duplicate",
                             json={"producer_id": str(self.p2), "name": "Colle del Limone"}, headers=self.auth(self.admin_token))
        self.assertIsNone(r.json()["existing_product"])
        r = self.client.post(f"{API}/products/import/check-duplicate",
                             json={"producer_id": str(self.p1), "name": "x"}, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 403)

    def test_confirm_never_creates_same_wine_twice(self):
        wine = {"name": "Colle del Limone – Falanghina del Molise", "producer_id": str(self.catabbo), "action": "create",
                "category": "VINO_BIANCO"}
        twin = dict(wine, name="Colle del Limone")
        r = self.client.post(f"{API}/products/import/confirm-batch", json={"wines": [wine, twin]},
                             headers=self.auth(self.admin_token)).json()
        self.assertEqual(r["created"], 1)
        self.assertEqual(r["skipped"], 1)
        self.assertEqual(len(r["duplicates"]), 1)
        self.assertEqual(run(self.db.products.count_documents({"producer_id": self.catabbo})), 1)

    def test_same_name_different_winery_is_not_duplicate(self):
        wine = {"name": "Colle del Limone", "action": "create", "category": "VINO_BIANCO"}
        r = self.client.post(f"{API}/products/import/confirm-batch",
                             json={"wines": [dict(wine, producer_id=str(self.catabbo)), dict(wine, producer_id=str(self.p1))]},
                             headers=self.auth(self.admin_token)).json()
        self.assertEqual(r["created"], 2)


if __name__ == "__main__":
    unittest.main()


class BatchCheckTests(AIConfigMixin, BaseTest):
    def test_check_batch(self):
        wines = [
            {"producer_id": "a", "name": "Colle del Limone – Falanghina del Molise", "source_file": "1.pdf"},
            {"producer_id": "a", "name": "Tintilia del Molise", "source_file": "1.pdf"},
            {"producer_id": "a", "name": "Colle del Limone", "source_file": "2.pdf"},
            {"producer_id": "b", "name": "Colle del Limone", "source_file": "3.pdf"},
            {"producer_id": "a", "name": "Tintilia del Molise", "is_riserva": True, "source_file": "4.pdf"},
        ]
        r = self.client.post(f"{API}/products/import/check-batch", json={"wines": wines}, headers=self.auth(self.admin_token))
        dup = [x["duplicate_of_index"] for x in r.json()["results"]]
        self.assertEqual(dup, [None, None, 0, None, None])
