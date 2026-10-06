"""Eventi: creazione da cantina e amministratore, pagine pubbliche, richieste di prenotazione,
annullamento, duplicazione e visibilita'."""
import unittest
from datetime import datetime, timedelta

from tests.test_security import API, BaseTest, run
from app.services.events import date_label, rome_now


def future(days=7, hour=18):
    return (rome_now() + timedelta(days=days)).replace(hour=hour, minute=0, second=0, microsecond=0)


def event_body(**extra):
    start = future()
    body = {
        "title": "Degustazione in vigna",
        "type": "DEGUSTAZIONE",
        "description": "Tre vini al tramonto.",
        "dates": [{"start": start.isoformat(), "end": (start + timedelta(hours=3)).isoformat()}],
        "use_producer_address": True,
        "price_type": "PAID",
        "price_text": "20 € a persona",
        "booking_mode": "REQUEST",
        "status": "PUBLISHED",
    }
    body.update(extra)
    return body


class EventTestBase(BaseTest):
    def create(self, token, **extra):
        r = self.client.post(f"{API}/events", json=event_body(**extra), headers=self.auth(token))
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def outbox(self, template):
        return [d for d in self.db.email_outbox.docs if d["template"] == template]

    def public_slugs(self, **params):
        r = self.client.get(f"{API}/events", params=params)
        self.assertEqual(r.status_code, 200, r.text)
        return [e["slug"] for e in r.json()]


class CreateAndListTests(EventTestBase):
    def test_winery_event_is_published_and_admin_notified(self):
        ev = self.create(self.p1_token, producer_id=str(self.p2), participant_ids=[str(self.p2)])
        self.assertEqual(ev["slug"], "degustazione-in-vigna")
        self.assertEqual(ev["organizer"]["id"], str(self.p1))      # sempre la propria cantina
        self.assertEqual(ev["participants"], [])                   # i partecipanti li sceglie l'admin
        self.assertEqual(ev["location"]["city"], "Campobasso")     # indirizzo della cantina
        self.assertIn(ev["slug"], self.public_slugs())
        self.assertEqual(len(self.outbox("nuovo_evento_admin")), 1)

    def test_drafts_hidden_pending_and_past_are_not_public(self):
        draft = self.create(self.p1_token, title="Bozza di evento", status="DRAFT")
        pending = self.create(self.pending_token, title="Evento cantina in attesa")
        past_start = rome_now() - timedelta(days=3)
        past = self.create(self.p1_token, title="Evento passato",
                           dates=[{"start": past_start.isoformat(), "end": (past_start + timedelta(hours=2)).isoformat()}])
        hidden = self.create(self.p1_token, title="Evento nascosto")
        r = self.client.put(f"{API}/events/{hidden['id']}/visibility", json={"hidden": True},
                            headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 200)
        slugs = self.public_slugs()
        for e in (draft, pending, past, hidden):
            self.assertNotIn(e["slug"], slugs)
        self.assertIn(past["slug"], self.public_slugs(past="true"))
        self.assertEqual(self.client.get(f"{API}/events/{draft['slug']}").status_code, 404)
        # l'organizzatore vede comunque l'anteprima della bozza
        r = self.client.get(f"{API}/events/{draft['slug']}", headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["can_edit"])

    def test_only_admin_can_hide(self):
        ev = self.create(self.p1_token)
        r = self.client.put(f"{API}/events/{ev['id']}/visibility", json={"hidden": True}, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 403)

    def test_territory_event_with_participants(self):
        ev = self.create(self.admin_token, title="Festa della Tintilia", type="FIERA", producer_id=None,
                         use_producer_address=False, participant_ids=[str(self.p1), str(self.p2), str(self.p_pending)],
                         location={"name": "Piazza Municipio", "city": "Larino", "province": "CB"},
                         product_ids=[str(self.pub1), str(self.pub2)], price_type="FREE")
        self.assertIsNone(ev["organizer"])
        self.assertEqual(ev["location"]["city"], "Larino")
        public = self.client.get(f"{API}/events/{ev['slug']}").json()
        # le cantine non ancora approvate non compaiono tra i partecipanti
        self.assertEqual([p["name"] for p in public["participants"]], ["Cantina Uno", "Cantina Due"])
        self.assertEqual({w["name"] for w in public["wines"]}, {"Tintilia Pubblicata", "Biferno Rosso"})
        self.assertIn(ev["slug"], self.public_slugs(producer=str(self.p2)))
        self.assertIn(ev["slug"], self.public_slugs(product=str(self.pub1)))
        self.assertIn(ev["slug"], self.public_slugs(city="larino", free="true"))
        self.assertNotIn(ev["slug"], self.public_slugs(city="Termoli"))
        # la cantina partecipante lo vede nell'area riservata ma non lo modifica
        managed = self.client.get(f"{API}/events/manage", headers=self.auth(self.p2_token)).json()
        self.assertEqual([(e["slug"], e["can_edit"]) for e in managed], [(ev["slug"], False)])
        r = self.client.put(f"{API}/events/{ev['id']}", json=event_body(), headers=self.auth(self.p2_token))
        self.assertEqual(r.status_code, 403)

    def test_territory_event_needs_a_place(self):
        r = self.client.post(f"{API}/events", json=event_body(producer_id=None, use_producer_address=False),
                             headers=self.auth(self.admin_token))
        self.assertEqual(r.status_code, 400)
        self.assertIn("dove si svolge", r.json()["detail"])

    def test_winery_cannot_link_other_wineries_wines(self):
        ev = self.create(self.p1_token, product_ids=[str(self.pub1), str(self.pub2)])
        self.assertEqual([w["name"] for w in ev["wines"]], ["Tintilia Pubblicata"])

    def test_validation_messages(self):
        start = future()
        bad = event_body(dates=[{"start": start.isoformat(), "end": (start - timedelta(hours=1)).isoformat()}])
        r = self.client.post(f"{API}/events", json=bad, headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 422)
        self.assertIn("fine dell'evento", r.json()["detail"])
        r = self.client.post(f"{API}/events", json=event_body(booking_mode="EXTERNAL"), headers=self.auth(self.p1_token))
        self.assertIn("link per la prenotazione", r.json()["detail"])

    def test_recurring_event_sorted_by_next_date(self):
        soon = self.create(self.p1_token, title="Evento tra tre giorni",
                           dates=[{"start": future(3).isoformat()}])
        weekly = self.create(self.p1_token, title="Ogni settimana",
                             dates=[{"start": (rome_now() - timedelta(days=5)).isoformat()},
                                    {"start": future(1).isoformat()}, {"start": future(8).isoformat()}])
        listed = self.client.get(f"{API}/events").json()
        self.assertEqual([e["slug"] for e in listed][:2], [weekly["slug"], soon["slug"]])
        self.assertEqual(listed[0]["next_date"]["start"][:10], future(1).isoformat()[:10])

    def test_update_and_slug(self):
        ev = self.create(self.p1_token)
        r = self.client.put(f"{API}/events/{ev['id']}", json=event_body(title="Cena in cantina", type="CENA"),
                            headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["slug"], "cena-in-cantina")
        r = self.client.put(f"{API}/events/{ev['id']}", json=event_body(), headers=self.auth(self.p2_token))
        self.assertEqual(r.status_code, 403)

    def test_duplicate_is_draft(self):
        ev = self.create(self.p1_token)
        r = self.client.post(f"{API}/events/{ev['id']}/duplicate", headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 200)
        copy = run(self.db.events.find_one({"slug": r.json()["slug"]}))
        self.assertEqual(copy["status"], "DRAFT")
        self.assertIn("(copia)", copy["title"])

    def test_deleting_winery_removes_its_events(self):
        own = self.create(self.p2_token)
        territory = self.create(self.admin_token, producer_id=None, use_producer_address=False,
                                location={"city": "Termoli"}, participant_ids=[str(self.p1), str(self.p2)])
        self.client.delete(f"{API}/producers/{self.p2}", headers=self.auth(self.admin_token))
        self.assertIsNone(run(self.db.events.find_one({"slug": own["slug"]})))
        remaining = run(self.db.events.find_one({"slug": territory["slug"]}))
        self.assertEqual(remaining["participant_ids"], [self.p1])


class BookingTests(EventTestBase):
    def request(self, event_id, **extra):
        body = {"user_name": "Maria Rossi", "user_email": "maria@example.com", "people": 3,
                "message": "Una persona è celiaca", "privacy_accepted": True}
        body.update(extra)
        return self.client.post(f"{API}/events/{event_id}/requests", json=body)

    def test_request_reaches_winery_and_visitor(self):
        ev = self.create(self.p1_token)
        r = self.request(ev["id"])
        self.assertEqual(r.status_code, 200, r.text)
        to_winery = self.outbox("nuova_prenotazione_evento")
        self.assertEqual(to_winery[0]["to"], ["uno@test.it"])
        self.assertIn("3 persone", to_winery[0]["subject"])
        self.assertEqual(self.outbox("conferma_prenotazione_evento")[0]["to"], ["maria@example.com"])
        inbox = self.client.get(f"{API}/inquiries", headers=self.auth(self.p1_token)).json()
        self.assertEqual(inbox[0]["message_type"], "EVENTO")
        self.assertEqual(inbox[0]["event_title"], "Degustazione in vigna")
        self.assertEqual(inbox[0]["event_slug"], ev["slug"])
        self.assertEqual(inbox[0]["people"], 3)
        managed = self.client.get(f"{API}/events/manage", headers=self.auth(self.p1_token)).json()
        self.assertEqual(managed[0]["requests_count"], 1)

    def test_winery_without_email_falls_back_to_admin(self):
        ev = self.create(self.p2_token)
        run(self.db.users.delete_many({"producer_id": self.p2}))
        self.request(ev["id"])
        self.assertEqual(self.outbox("nuova_prenotazione_evento")[0]["to"], ["admin@test.it"])

    def test_request_rules(self):
        ev = self.create(self.p1_token)
        self.assertEqual(self.request(ev["id"], privacy_accepted=False).status_code, 422)
        self.assertEqual(self.request(ev["id"], date_index=5).status_code, 400)
        no_booking = self.create(self.p1_token, title="Ingresso libero", booking_mode="NONE")
        self.assertEqual(self.request(no_booking["id"]).status_code, 400)
        draft = self.create(self.p1_token, title="Bozza", status="DRAFT")
        self.assertEqual(self.request(draft["id"]).status_code, 404)

    def test_past_date_of_recurring_event_is_refused(self):
        ev = self.create(self.p1_token, dates=[{"start": (rome_now() - timedelta(days=2)).isoformat()},
                                               {"start": future(2).isoformat()}])
        self.assertEqual(self.request(ev["id"], date_index=0).status_code, 400)
        self.assertEqual(self.request(ev["id"], date_index=1).status_code, 200)

    def test_territory_event_request_goes_to_contact_or_admin(self):
        ev = self.create(self.admin_token, producer_id=None, use_producer_address=False, location={"city": "Larino"})
        self.request(ev["id"])
        self.assertEqual(self.outbox("nuova_prenotazione_evento")[0]["to"], ["admin@test.it"])
        with_contact = self.create(self.admin_token, title="Con contatto", producer_id=None,
                                   use_producer_address=False, location={"city": "Larino"},
                                   contact_email="proloco@example.com")
        self.request(with_contact["id"], user_email="luca@example.com")
        self.assertEqual(self.outbox("nuova_prenotazione_evento")[1]["to"], ["proloco@example.com"])
        # solo l'amministratore vede queste richieste
        admin_inbox = self.client.get(f"{API}/inquiries", headers=self.auth(self.admin_token)).json()
        self.assertEqual(sum(1 for i in admin_inbox if i["message_type"] == "EVENTO" and i["producer_id"] is None), 2)
        self.assertEqual(self.client.get(f"{API}/inquiries", headers=self.auth(self.p1_token)).json(), [])

    def test_cancel_notifies_requesters_once(self):
        ev = self.create(self.p1_token)
        self.request(ev["id"])
        self.request(ev["id"], user_email="MARIA@example.com")
        self.request(ev["id"], user_name="Luca", user_email="luca@example.com")
        r = self.client.post(f"{API}/events/{ev['id']}/cancel", json={"message": "Maltempo"},
                             headers=self.auth(self.p1_token))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["notified"], 2)
        mails = self.outbox("evento_annullato")
        self.assertEqual(len(mails), 2)
        self.assertIn("Maltempo", mails[0]["text"])
        # resta raggiungibile (con l'avviso) ma non compare piu' tra gli eventi in programma
        self.assertEqual(self.client.get(f"{API}/events/{ev['slug']}").json()["status"], "CANCELLED")
        self.assertNotIn(ev["slug"], self.public_slugs())
        self.assertEqual(self.request(ev["id"]).status_code, 404)


class DateTests(unittest.TestCase):
    def test_rome_time_with_daylight_saving(self):
        self.assertEqual(rome_now(datetime(2026, 7, 1, 10, 0)), datetime(2026, 7, 1, 12, 0))
        self.assertEqual(rome_now(datetime(2026, 12, 1, 10, 0)), datetime(2026, 12, 1, 11, 0))
        # l'ora legale finisce l'ultima domenica di ottobre (25/10/2026) alle 01:00 UTC
        self.assertEqual(rome_now(datetime(2026, 10, 25, 0, 30)), datetime(2026, 10, 25, 2, 30))
        self.assertEqual(rome_now(datetime(2026, 10, 25, 1, 30)), datetime(2026, 10, 25, 2, 30))

    def test_labels(self):
        self.assertEqual(date_label({"start": datetime(2026, 10, 17, 18, 0), "end": datetime(2026, 10, 17, 21, 0)}),
                         "sabato 17 ottobre 2026, ore 18:00–21:00")
        self.assertEqual(date_label({"start": datetime(2026, 10, 17, 0, 0)}), "sabato 17 ottobre 2026")
        self.assertEqual(date_label({"start": datetime(2026, 10, 17, 10, 0), "end": datetime(2026, 10, 19, 20, 0)}),
                         "dal 17 al 19 ottobre 2026")
