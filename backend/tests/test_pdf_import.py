"""Test dell'importazione dei vini da PDF (servizio IA simulato: nessuna chiamata di rete)."""
import copy
import io
import json
import os
import unittest
from datetime import datetime
from unittest import mock

from tests.test_security import BaseTest, API, run
from app.core.config import settings
from app.services import ai_extractor
from app.services.pdf_importer import CANONICAL_PAIRINGS, VALID_SINGLE_GRAPES, normalize_wine

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
with open(os.path.join(FIXTURES, "catabbo_ai_response.json"), encoding="utf-8") as f:
    CATABBO_AI = json.load(f)
with open(os.path.join(FIXTURES, "catabbo_screenshot.pdf"), "rb") as f:
    CATABBO_PDF = f.read()


def text_pdf(lines):
    """PDF testuale generato al volo (per il parser senza IA)."""
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for line in lines:
        c.drawString(40, y, line)
        y -= 16
    c.save()
    return buf.getvalue()


class FakeResponse:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


def gemini_reply(data):
    return FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": json.dumps(data, ensure_ascii=False)}]}}]})


def anthropic_reply(data):
    return FakeResponse(200, {"content": [{"type": "tool_use", "name": "registra_vini", "input": data}]})


class AIConfigMixin:
    def setUp(self):
        super().setUp()
        self._saved = (settings.AI_PROVIDER, settings.GEMINI_API_KEY, settings.ANTHROPIC_API_KEY)
        settings.AI_PROVIDER, settings.GEMINI_API_KEY, settings.ANTHROPIC_API_KEY = "auto", None, None
        # cantina Catabbo con sito web, per il riconoscimento automatico
        self.catabbo = run(self.db.producers.insert_one({
            "company_name": "Catabbo", "slug": "catabbo", "status": "APPROVED",
            "contacts": {"website": "https://www.catabbo.it"}, "address": {"city": "San Martino in Pensilis"},
            "created_at": datetime.utcnow(),
        })).inserted_id

    def tearDown(self):
        settings.AI_PROVIDER, settings.GEMINI_API_KEY, settings.ANTHROPIC_API_KEY = self._saved
        super().tearDown()

    def parse(self, pdf=CATABBO_PDF, name="catabbo.pdf", **data):
        return self.client.post(f"{API}/products/import/parse-pdfs", data=data,
                                files={"files": (name, pdf, "application/pdf")}, headers=self.auth(self.admin_token))


class ParsePdfTests(AIConfigMixin, BaseTest):
    def test_ai_status(self):
        r = self.client.get(f"{API}/products/import/ai-status", headers=self.auth(self.admin_token))
        self.assertEqual(r.json()["configured"], False)
        settings.GEMINI_API_KEY = "k"
        r = self.client.get(f"{API}/products/import/ai-status", headers=self.auth(self.admin_token))
        self.assertEqual(r.json(), {"configured": True, "provider": "gemini", "model": settings.GEMINI_MODEL})

    def test_screenshot_pdf_without_ai_gives_clear_error(self):
        r = self.parse()
        self.assertEqual(r.status_code, 200, r.text)
        f = r.json()["files"][0]
        self.assertEqual(f["status"], "error")
        self.assertIn("GEMINI_API_KEY", f["error"])

    def test_gemini_extraction_end_to_end(self):
        settings.GEMINI_API_KEY = "test-key"
        with mock.patch.object(ai_extractor.requests, "post", return_value=gemini_reply(CATABBO_AI)) as post:
            r = self.parse()
        self.assertEqual(r.status_code, 200, r.text)

        # richiesta inviata a Gemini: PDF allegato come documento + schema JSON vincolato
        url, kwargs = post.call_args[0][0], post.call_args[1]
        self.assertIn(f"models/{settings.GEMINI_MODEL}:generateContent", url)
        self.assertEqual(kwargs["headers"]["x-goog-api-key"], "test-key")
        body = kwargs["json"]
        self.assertEqual(body["contents"][0]["parts"][0]["inline_data"]["mime_type"], "application/pdf")
        self.assertEqual(body["generationConfig"]["responseMimeType"], "application/json")
        self.assertNotIn('"null"', json.dumps(body["generationConfig"]["responseSchema"]))
        self.assertIn("prodotti correlati", body["contents"][0]["parts"][1]["text"])

        f = r.json()["files"][0]
        self.assertEqual(f["status"], "ok")
        self.assertEqual(f["method"], "ai:gemini")
        self.assertEqual(f["producer_id"], str(self.catabbo))  # cantina riconosciuta
        self.assertEqual(len(f["wines"]), 1)
        w = f["wines"][0]
        self.assertEqual(w["name"], "Colle del Limone – Falanghina del Molise")
        self.assertEqual(w["category"], "VINO_BIANCO")
        self.assertEqual(w["denominazione"], "DOP")
        self.assertIsNone(w["vintage_year"])  # "prima annata 2004" non e' l'annata
        self.assertEqual(w["grape_varieties"], ["Falanghina"])
        self.assertEqual(w["serving_temperature"], "10-12°C")
        self.assertEqual(w["indicative_price"], "15,00 €")
        self.assertEqual(w["action"], "create")
        attrs = {a["name"]: a["value"] for a in w["custom_attributes"]}
        self.assertEqual(attrs["Zona di Produzione"], "San Martino in Pensilis")
        self.assertEqual(attrs["Altitudine Vigneto"], "300 m s.l.m.")
        self.assertEqual(attrs["Allevamento"], "Cordone speronato basso")
        self.assertIn("2 mesi in bottiglia", attrs["Affinamento"])
        self.assertIn("6 mesi", attrs["Affinamento"])
        self.assertNotIn("Denominazione", attrs)
        self.assertNotIn("Temperatura di Servizio", attrs)
        self.assertGreaterEqual(len(attrs), 14)
        self.assertIn("Pesce & Frutti di Mare", w["food_pairings"])
        self.assertEqual(r.json()["count"], 1)
        # nessuna scrittura nel DB durante l'analisi
        self.assertEqual(run(self.db.products.count_documents({"producer_id": self.catabbo})), 0)

    def test_anthropic_extraction(self):
        settings.ANTHROPIC_API_KEY = "sk-test"
        with mock.patch.object(ai_extractor.requests, "post", return_value=anthropic_reply(CATABBO_AI)) as post:
            r = self.parse()
        body = post.call_args[1]["json"]
        self.assertEqual(body["tool_choice"], {"type": "tool", "name": "registra_vini"})
        self.assertEqual(body["messages"][0]["content"][0]["type"], "document")
        self.assertEqual(post.call_args[1]["headers"]["x-api-key"], "sk-test")
        self.assertEqual(r.json()["files"][0]["wines"][0]["name"], "Colle del Limone – Falanghina del Molise")

    def test_existing_wine_is_detected(self):
        run(self.db.products.insert_one({"name": "Colle del Limone – Falanghina del Molise", "slug": "colle-del-limone",
                                         "producer_id": self.catabbo, "status": "PUBLISHED"}))
        settings.GEMINI_API_KEY = "k"
        with mock.patch.object(ai_extractor.requests, "post", return_value=gemini_reply(CATABBO_AI)):
            w = self.parse().json()["files"][0]["wines"][0]
        self.assertEqual(w["action"], "update")
        self.assertEqual(w["existing_product"]["slug"], "colle-del-limone")

    def test_forced_producer_overrides_detection(self):
        settings.GEMINI_API_KEY = "k"
        with mock.patch.object(ai_extractor.requests, "post", return_value=gemini_reply(CATABBO_AI)):
            f = self.parse(producer_id=str(self.p1)).json()["files"][0]
        self.assertEqual(f["producer_id"], str(self.p1))

    def test_unknown_producer_left_empty(self):
        data = copy.deepcopy(CATABBO_AI)
        data["producer"] = {"name": "Tenuta Sconosciuta", "city": None, "website": None}
        settings.GEMINI_API_KEY = "k"
        with mock.patch.object(ai_extractor.requests, "post", return_value=gemini_reply(data)):
            f = self.parse().json()["files"][0]
        self.assertEqual(f["producer_id"], "")
        self.assertEqual(f["wines"][0]["producer_id"], "")

    def test_multiple_wines_in_one_pdf(self):
        data = copy.deepcopy(CATABBO_AI)
        second = copy.deepcopy(data["wines"][0])
        second.update({"name": "I Diecettari – Molise Rosso DOP", "category": "VINO_ROSSO", "grape_varieties": [{"name": "Montepulciano", "percentage": None}]})
        data["wines"].append(second)
        settings.GEMINI_API_KEY = "k"
        with mock.patch.object(ai_extractor.requests, "post", return_value=gemini_reply(data)):
            f = self.parse().json()["files"][0]
        self.assertEqual([w["name"] for w in f["wines"]], ["Colle del Limone – Falanghina del Molise", "I Diecettari – Molise Rosso"])

    def test_ai_errors_are_readable(self):
        settings.GEMINI_API_KEY = "bad"
        with mock.patch.object(ai_extractor.requests, "post", return_value=FakeResponse(403, {"error": {"message": "denied"}})):
            f = self.parse().json()["files"][0]
        self.assertEqual(f["status"], "error")
        self.assertIn("Chiave API", f["error"])
        with mock.patch.object(ai_extractor.requests, "post", return_value=FakeResponse(429, {})):
            self.assertIn("Limite", self.parse().json()["files"][0]["error"])

    def test_overloaded_model_retries_then_falls_back(self):
        settings.GEMINI_API_KEY = "k"
        busy = FakeResponse(503, {"error": {"message": "This model is currently experiencing high demand."}})
        calls = []

        def fake_post(url, **kw):
            calls.append(url)
            return busy if settings.GEMINI_MODEL in url else gemini_reply(CATABBO_AI)

        with mock.patch.object(ai_extractor.requests, "post", side_effect=fake_post), \
                mock.patch.object(ai_extractor.time, "sleep") as sleep:
            f = self.parse().json()["files"][0]
        self.assertEqual(f["status"], "ok", f)
        fallback = ai_extractor.gemini_models()[1]
        self.assertEqual(f["model"], fallback)
        self.assertEqual(sum(settings.GEMINI_MODEL in u for u in calls), 3)  # 1 tentativo + 2 riprove
        self.assertEqual(sleep.call_count, 2)

    def test_quota_exhausted_switches_model_immediately(self):
        settings.GEMINI_API_KEY = "k"
        calls = []

        def fake_post(url, **kw):
            calls.append(url)
            return FakeResponse(429, {}) if len(calls) == 1 else gemini_reply(CATABBO_AI)

        with mock.patch.object(ai_extractor.requests, "post", side_effect=fake_post), \
                mock.patch.object(ai_extractor.time, "sleep") as sleep:
            f = self.parse().json()["files"][0]
        self.assertEqual(f["status"], "ok")
        self.assertEqual(sleep.call_count, 0)
        self.assertEqual(len(calls), 2)

    def test_truncated_json_retries_then_falls_back(self):
        settings.GEMINI_API_KEY = "k"
        full = json.dumps(CATABBO_AI, ensure_ascii=False)
        truncated = FakeResponse(200, {"candidates": [{"finishReason": "MAX_TOKENS",
                                                       "content": {"parts": [{"text": full[:200]}]}}]})
        calls = []

        def fake_post(url, json=None, **kw):
            calls.append((url, json["generationConfig"]["temperature"]))
            return truncated if settings.GEMINI_MODEL in url else gemini_reply(CATABBO_AI)

        with mock.patch.object(ai_extractor.requests, "post", side_effect=fake_post), \
                mock.patch.object(ai_extractor.time, "sleep") as sleep:
            f = self.parse().json()["files"][0]
        self.assertEqual(f["status"], "ok", f)
        self.assertEqual(f["model"], ai_extractor.gemini_models()[1])
        # due tentativi sul modello principale (il secondo meno rigido), poi il modello di riserva
        self.assertEqual([t for u, t in calls if settings.GEMINI_MODEL in u], [0, 0.4])
        self.assertEqual(sleep.call_count, 0)

    def test_recitation_retries_asking_to_rephrase(self):
        settings.GEMINI_API_KEY = "k"
        blocked = FakeResponse(200, {"candidates": [{"finishReason": "RECITATION",
                                                     "content": {"parts": [{"text": '{"wines": [{"descr'}]}}]})
        prompts = []

        def fake_post(url, json=None, **kw):
            text = json["contents"][0]["parts"][1]["text"]
            prompts.append(text)
            return gemini_reply(CATABBO_AI) if "riformulalo" in text else blocked

        with mock.patch.object(ai_extractor.requests, "post", side_effect=fake_post):
            f = self.parse().json()["files"][0]
        self.assertEqual(f["status"], "ok", f)
        self.assertEqual(f["model"], settings.GEMINI_MODEL)  # stesso modello, secondo tentativo
        self.assertEqual(len(prompts), 2)
        self.assertNotIn("riformulalo", prompts[0])

    def test_json_in_code_fence_is_accepted(self):
        settings.GEMINI_API_KEY = "k"
        text = "```json\n" + json.dumps(CATABBO_AI, ensure_ascii=False) + "\n```"
        reply = FakeResponse(200, {"candidates": [{"content": {"parts": [
            {"text": "ragionamento", "thought": True}, {"text": text}]}}]})
        with mock.patch.object(ai_extractor.requests, "post", return_value=reply):
            f = self.parse().json()["files"][0]
        self.assertEqual(f["status"], "ok", f)

    def test_invalid_json_everywhere_gives_readable_error(self):
        settings.GEMINI_API_KEY = "k"
        bad = FakeResponse(200, {"candidates": [{"finishReason": "MAX_TOKENS",
                                                 "content": {"parts": [{"text": '{"wines": [{"name": "Le'}]}}]})
        with mock.patch.object(ai_extractor.requests, "post", return_value=bad), \
                mock.patch.object(ai_extractor.time, "sleep"):
            f = self.parse().json()["files"][0]
        self.assertEqual(f["status"], "error")
        self.assertIn("troncata", f["error"])

    def test_all_models_busy_gives_readable_error(self):
        settings.GEMINI_API_KEY = "k"
        with mock.patch.object(ai_extractor.requests, "post", return_value=FakeResponse(503, {})), \
                mock.patch.object(ai_extractor.time, "sleep"):
            f = self.parse().json()["files"][0]
        self.assertEqual(f["status"], "error")
        self.assertIn("sovraccarico", f["error"])

    def test_text_pdf_without_ai(self):
        pdf = text_pdf([
            "Tintilia del Molise Riserva",
            "Denominazione: Tintilia del Molise DOC",
            "Uve: Tintilia 100%",
            "Gradazione alcolica: 14,5% vol",
            "Sistema di allevamento: Guyot",
            "Affinamento: 18 mesi in barrique",
            "Temperatura di servizio: 16-18 C",
        ])
        f = self.parse(pdf=pdf, name="tintilia.pdf", producer_id=str(self.p1)).json()["files"][0]
        self.assertEqual(f["status"], "ok", f)
        self.assertEqual(f["method"], "text")
        w = f["wines"][0]
        self.assertEqual(w["name"], "Tintilia del Molise Riserva")
        self.assertTrue(w["is_riserva"])
        self.assertEqual(w["denominazione"], "DOC")
        self.assertEqual(w["alcohol_degrees"], 14.5)
        self.assertEqual(w["grape_varieties"], ["Tintilia"])
        self.assertEqual(w["serving_temperature"], "16-18°C")
        self.assertEqual(w["category"], "VINO_ROSSO")
        attrs = {a["name"]: a["value"] for a in w["custom_attributes"]}
        self.assertEqual(attrs["Allevamento"], "Guyot")
        self.assertEqual(attrs["Affinamento"], "18 mesi in barrique")
        # nessun valore inventato
        self.assertEqual(w["tasting_notes"], {"visual": "", "olfactory": "", "taste": ""})
        self.assertNotIn("Allergeni", attrs)

    def _image(self, fmt="JPEG", size=(900, 1400)):
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", size, "white").save(buf, fmt)
        return buf.getvalue()

    def test_image_with_gemini(self):
        settings.GEMINI_API_KEY = "k"
        with mock.patch.object(ai_extractor.requests, "post", return_value=gemini_reply(CATABBO_AI)) as post:
            f = self.parse(pdf=self._image(), name="scheda.jpg").json()["files"][0]
        self.assertEqual(f["status"], "ok", f)
        self.assertEqual(f["file_type"], "image")
        inline = post.call_args[1]["json"]["contents"][0]["parts"][0]["inline_data"]
        self.assertEqual(inline["mime_type"], "image/jpeg")
        self.assertEqual(f["wines"][0]["name"], "Colle del Limone – Falanghina del Molise")

    def test_png_with_claude_uses_image_block(self):
        settings.ANTHROPIC_API_KEY = "sk"
        with mock.patch.object(ai_extractor.requests, "post", return_value=anthropic_reply(CATABBO_AI)) as post:
            f = self.parse(pdf=self._image("PNG"), name="scheda.png").json()["files"][0]
        block = post.call_args[1]["json"]["messages"][0]["content"][0]
        self.assertEqual(block["type"], "image")
        self.assertEqual(block["source"]["media_type"], "image/png")
        self.assertEqual(f["status"], "ok")

    def test_large_image_is_resized(self):
        import base64
        from PIL import Image
        settings.GEMINI_API_KEY = "k"
        with mock.patch.object(ai_extractor.requests, "post", return_value=gemini_reply(CATABBO_AI)) as post:
            self.parse(pdf=self._image("PNG", (5000, 7000)), name="grande.png")
        inline = post.call_args[1]["json"]["contents"][0]["parts"][0]["inline_data"]
        sent = Image.open(io.BytesIO(base64.b64decode(inline["data"])))
        self.assertLessEqual(max(sent.size), 3000)
        self.assertEqual(inline["mime_type"], "image/jpeg")

    def test_image_without_ai_gives_clear_error(self):
        f = self.parse(pdf=self._image(), name="scheda.jpg").json()["files"][0]
        self.assertEqual(f["status"], "error")
        self.assertIn("immagine", f["error"])

    def test_fake_image_extension_rejected(self):
        settings.GEMINI_API_KEY = "k"
        f = self.parse(pdf=b"<html>non sono un'immagine</html>", name="finta.jpg").json()["files"][0]
        self.assertEqual(f["status"], "error")
        self.assertIn("Formato non supportato", f["error"])

    def test_non_pdf_rejected_per_file(self):
        f = self.parse(pdf=b"not a pdf").json()["files"][0]
        self.assertEqual(f["status"], "error")


class ConfirmImportTests(AIConfigMixin, BaseTest):
    def wine(self, **over):
        w = normalize_wine(CATABBO_AI["wines"][0], [], VALID_SINGLE_GRAPES, CANONICAL_PAIRINGS)
        w.update({"producer_id": str(self.catabbo), "action": "create"})
        w.update(over)
        return w

    def confirm(self, wines, **extra):
        return self.client.post(f"{API}/products/import/confirm-batch", json={"wines": wines, **extra},
                                headers=self.auth(self.admin_token))

    def test_create_full_product(self):
        r = self.confirm([self.wine()], status="DRAFT")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["created"], 1)
        doc = run(self.db.products.find_one({"producer_id": self.catabbo}))
        self.assertEqual(doc["status"], "DRAFT")
        self.assertEqual(doc["slug"], "colle-del-limone-falanghina-del-molise")
        self.assertEqual(doc["photos"], [])
        self.assertEqual(doc["grape_varieties"], ["Falanghina"])
        self.assertGreaterEqual(len(doc["custom_attributes"]), 14)
        self.assertTrue(doc["tasting_notes"]["olfactory"].startswith("Profumi intensi"))
        # tassonomie aggiornate
        self.assertIsNotNone(run(self.db.attributes.find_one({"name": "Tipologia del Terreno"})))
        self.assertIsNotNone(run(self.db.grapes.find_one({"name": "Falanghina"})))

    def test_update_is_non_destructive(self):
        pid = run(self.db.products.insert_one({
            "name": "Colle del Limone – Falanghina del Molise", "slug": "colle-del-limone-falanghina-del-molise",
            "producer_id": self.catabbo, "status": "PUBLISHED", "alcohol_degrees": 13.0, "photos": ["/uploads/x.webp"],
            "custom_attributes": [{"name": "Formato", "value": "75 cl"}, {"name": "Allevamento", "value": "vecchio"}],
            "tasting_notes": {"visual": "Giallo paglierino", "olfactory": "", "taste": ""},
        })).inserted_id
        r = self.confirm([self.wine(action="update", existing_id=str(pid))])
        self.assertEqual(r.json()["updated"], 1, r.text)
        doc = run(self.db.products.find_one({"_id": pid}))
        self.assertEqual(doc["alcohol_degrees"], 13.0)          # non cancellata dal PDF senza gradazione
        self.assertEqual(doc["photos"], ["/uploads/x.webp"])    # foto conservate
        self.assertEqual(doc["tasting_notes"]["visual"], "Giallo paglierino")
        attrs = {a["name"]: a["value"] for a in doc["custom_attributes"]}
        self.assertEqual(attrs["Formato"], "75 cl")               # attributo esistente conservato
        self.assertEqual(attrs["Allevamento"], "Cordone speronato basso")  # aggiornato
        self.assertEqual(run(self.db.products.count_documents({"producer_id": self.catabbo})), 1)

    def test_skip_and_missing_producer(self):
        r = self.confirm([self.wine(action="skip"), self.wine(producer_id="")])
        self.assertEqual(r.json()["skipped"], 1)
        self.assertEqual(len(r.json()["errors"]), 1)
        self.assertEqual(r.json()["created"], 0)

    def test_default_producer_used_when_missing(self):
        r = self.confirm([self.wine(producer_id="")], producer_id=str(self.p1))
        self.assertEqual(r.json()["created"], 1, r.text)
        self.assertEqual(run(self.db.products.count_documents({"producer_id": self.p1, "name": {"$regex": "Colle"}})), 1)

    def test_same_name_other_winery_gets_distinct_slug(self):
        self.confirm([self.wine()])
        self.confirm([self.wine(producer_id=str(self.p1))])
        slugs = sorted(d["slug"] for d in self.db.products.docs if "Colle" in d.get("name", ""))
        self.assertEqual(len(set(slugs)), 2)

    def test_external_pdf_url_not_accepted(self):
        self.confirm([self.wine(technical_sheet_pdf="https://evil.example/x.pdf")])
        doc = run(self.db.products.find_one({"producer_id": self.catabbo}))
        self.assertEqual(doc["technical_sheet_pdf"], "")


if __name__ == "__main__":
    unittest.main()


class OrganicTests(unittest.TestCase):
    """Vini biologici: un solo standard, "Tipo Vino" = "Biologico" (come nei vini inseriti a mano)."""

    def norm(self, **over):
        raw = copy.deepcopy(CATABBO_AI["wines"][0])
        raw.update(over)
        return normalize_wine(raw, ["Tipo Vino", "Uvaggio"], VALID_SINGLE_GRAPES, CANONICAL_PAIRINGS)

    @staticmethod
    def attrs(w):
        return {a["name"]: a["value"] for a in w["custom_attributes"]}

    def tipo(self, w):
        return self.attrs(w).get("Tipo Vino")

    def test_non_organic_wine_has_no_tipo(self):
        w = self.norm()
        self.assertFalse(w["is_organic"])
        self.assertIsNone(self.tipo(w))

    def test_ai_flag_adds_tipo_vino(self):
        w = self.norm(is_organic=True)
        self.assertTrue(w["is_organic"])
        self.assertEqual(self.tipo(w), "Biologico")
        self.assertEqual(w["custom_attributes"][0]["name"], "Tipo Vino")

    def test_detected_from_text_even_without_ai_flag(self):
        for desc in ("Ottenuto da uve biologiche di Tintilia.", "Prodotto BIO certificato.",
                     "Vino da agricoltura biologica", "Organic wine from Molise"):
            with self.subTest(desc=desc):
                self.assertEqual(self.tipo(self.norm(description=desc)), "Biologico")

    def test_every_variant_becomes_the_same_attribute(self):
        base = CATABBO_AI["wines"][0]["attributes"]
        for extra in ({"name": "Certificazione", "value": "Biologico"},
                      {"name": "Certificazione", "value": "Biologico ICEA - IT-BIO-006"},
                      {"name": "Tipo", "value": "Vino Biologico"},
                      {"name": "Agricoltura", "value": "Biologica"},
                      {"name": "Biologico", "value": "Sì"},
                      {"name": "Tipo Vino", "value": "Biologico"}):
            with self.subTest(extra=extra):
                attrs = self.attrs(self.norm(attributes=base + [extra]))
                self.assertEqual(attrs.get("Tipo Vino"), "Biologico")
                for other in ("Certificazione", "Tipo", "Agricoltura", "Biologico"):
                    self.assertNotIn(other, attrs)

    def test_other_tipo_information_is_kept(self):
        base = CATABBO_AI["wines"][0]["attributes"]
        self.assertEqual(self.tipo(self.norm(attributes=base + [{"name": "Tipo", "value": "Vino fermo"}], is_organic=True)),
                         "Vino fermo; Biologico")
        self.assertEqual(self.tipo(self.norm(attributes=base + [{"name": "Tipo", "value": "Vino fermo biologico"}])),
                         "Vino fermo; Biologico")
        self.assertEqual(self.tipo(self.norm(attributes=base + [{"name": "Tipo", "value": "Vino fermo"}])), "Vino fermo")

    def test_non_organic_certification_untouched(self):
        attrs = self.attrs(self.norm(attributes=CATABBO_AI["wines"][0]["attributes"] + [{"name": "Certificazione", "value": "Vegan"}]))
        self.assertEqual(attrs["Certificazione"], "Vegan")
        self.assertNotIn("Tipo Vino", attrs)

    def test_false_positives(self):
        for desc in ("Grande biodiversità del vigneto.", "Studi di biologia del suolo.", "Vigneti in conversione al biologico.",
                     "Il biotipo locale di Tintilia."):
            with self.subTest(desc=desc):
                self.assertIsNone(self.tipo(self.norm(description=desc)))

    def test_master_attribute_casing_is_used(self):
        raw = copy.deepcopy(CATABBO_AI["wines"][0])
        raw["is_organic"] = True
        w = normalize_wine(raw, ["Tipo vino"], VALID_SINGLE_GRAPES, CANONICAL_PAIRINGS)
        self.assertEqual(w["custom_attributes"][0], {"name": "Tipo vino", "value": "Biologico"})

    def test_schema_and_prompt_include_organic(self):
        schema = ai_extractor.build_json_schema(CANONICAL_PAIRINGS)
        self.assertIn("is_organic", schema["properties"]["wines"]["items"]["properties"])
        self.assertIn("is_organic", schema["properties"]["wines"]["items"]["required"])
        gemini = ai_extractor._to_gemini_schema(schema)
        self.assertEqual(gemini["properties"]["wines"]["items"]["properties"]["is_organic"]["type"], "BOOLEAN")
        prompt = ai_extractor.build_prompt("x.pdf", [], [], CANONICAL_PAIRINGS)
        self.assertIn("is_organic", prompt)
        self.assertNotIn('"Certificazione": "Biologico', prompt)


class NormalizeCatalogScriptTests(BaseTest):
    def test_existing_wines_are_normalized(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "normalize_organic", os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "normalize_organic.py"))
        script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(script)

        imported = run(self.db.products.insert_one({"name": "Importato", "slug": "a", "producer_id": self.p1, "status": "PUBLISHED",
                                                    "custom_attributes": [{"name": "Formato", "value": "75 cl"},
                                                                          {"name": "Certificazione", "value": "Biologico"}]})).inserted_id
        manual = run(self.db.products.insert_one({"name": "A mano", "slug": "b", "producer_id": self.p1, "status": "PUBLISHED",
                                                  "custom_attributes": [{"name": "Tipo Vino", "value": "Biologico"}]})).inserted_id

        # anteprima: nessuna modifica
        self.assertEqual(run(script.normalize_catalog(self.db, apply=False)), 1)
        self.assertEqual(run(self.db.products.find_one({"_id": imported}))["custom_attributes"][1]["name"], "Certificazione")

        # applicazione
        self.assertEqual(run(script.normalize_catalog(self.db, apply=True)), 1)
        self.assertEqual(run(self.db.products.find_one({"_id": imported}))["custom_attributes"],
                         [{"name": "Tipo Vino", "value": "Biologico"}, {"name": "Formato", "value": "75 cl"}])
        self.assertEqual(run(self.db.products.find_one({"_id": manual}))["custom_attributes"],
                         [{"name": "Tipo Vino", "value": "Biologico"}])
        # seconda esecuzione: nulla da fare
        self.assertEqual(run(script.normalize_catalog(self.db, apply=True)), 0)
