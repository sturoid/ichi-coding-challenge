"""The reviewer's answers (PLAN section 2, "Reason codes and the reviewer's answers").

Guardrails: answers apply only to CNEs; an answer that contradicts a rule verdict is
Disputed; a changed row (fingerprint) makes the answer stale and the finding stays CNE.
Facts (net clear per type mark) run through the rules rather than overriding them.
"""
import copy
import unittest

from ichi.answers import template
from ichi.pipeline import run

from helpers import CNE, CODE_ANALYSIS_HTML, FAIL, NA, PASS, SCHEDULE_HTML


def base():
    return run(CODE_ANALYSIS_HTML, SCHEDULE_HTML)


class TestDecisions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fp = {f.id: f.fingerprint for f in base().findings}

    def run_with(self, decisions):
        return run(CODE_ANALYSIS_HTML, SCHEDULE_HTML, answers={"decisions": decisions}).by_id()

    def test_decision_on_cne_applies(self):
        by_id = self.run_with({"R303": {"verdict": FAIL, "why": "no window designated", "by": "J. Doe",
                                        "fingerprint": self.fp["R303"]}})
        r = by_id["R303"]
        self.assertEqual(r.verdict, FAIL)
        self.assertEqual(r.verdict_source, "checker decision")
        self.assertIn("J. Doe", r.reason)
        self.assertIn("no window designated", r.reason)
        self.assertFalse(any("Disputed" in x or "Stale" in x for x in r.flags))

    def test_decision_without_fingerprint_applies(self):
        by_id = self.run_with({"R102": {"verdict": NA, "why": "office, confirmed on plan", "by": "J. Doe"}})
        self.assertEqual(by_id["R102"].verdict, NA)
        self.assertEqual(by_id["R102"].verdict_source, "checker decision")

    def test_decision_on_rule_decided_fail_is_disputed(self):
        by_id = self.run_with({"W10": {"verdict": PASS, "why": "looks fine", "by": "J. Doe",
                                       "fingerprint": self.fp["W10"]}})
        f = by_id["W10"]
        self.assertEqual(f.verdict, FAIL, "a decision must not overturn a rule verdict")
        self.assertEqual(f.verdict_source, "rule")
        self.assertTrue(any("Disputed" in x for x in f.flags), f.flags)

    def test_decision_on_rule_decided_na_is_disputed(self):
        by_id = self.run_with({"W5": {"verdict": FAIL, "why": "", "by": "J. Doe"}})
        self.assertEqual(by_id["W5"].verdict, NA)
        self.assertTrue(any("Disputed" in x for x in by_id["W5"].flags))

    def test_agreeing_decision_on_decided_finding_is_not_disputed(self):
        by_id = self.run_with({"W10": {"verdict": FAIL, "why": "agree", "by": "J. Doe"}})
        self.assertEqual(by_id["W10"].verdict, FAIL)
        self.assertFalse(any("Disputed" in x for x in by_id["W10"].flags))

    def test_wrong_fingerprint_is_stale(self):
        by_id = self.run_with({"R303": {"verdict": FAIL, "why": "", "by": "J. Doe",
                                        "fingerprint": "room|303|21|303|36.0x48.0|casement|A"}})
        r = by_id["R303"]
        self.assertEqual(r.verdict, CNE, "stale answer must not apply")
        self.assertEqual(r.verdict_source, "rule")
        self.assertTrue(any("tale" in x for x in r.flags), r.flags)

    def test_changed_row_makes_answer_stale(self):
        # Take a fingerprint from the real schedule, then change W21's size: the answer for R303 is stale.
        fp = self.fp["R303"]
        changed = SCHEDULE_HTML.replace("<td>21</td>\n      <td>GUEST BED 303</td>\n      <td>2' - 6\"</td>",
                                        "<td>21</td>\n      <td>GUEST BED 303</td>\n      <td>3' - 6\"</td>")
        self.assertNotEqual(changed, SCHEDULE_HTML)
        by_id = run(CODE_ANALYSIS_HTML, changed, answers={"decisions": {"R303": {"verdict": FAIL, "by": "J. Doe", "fingerprint": fp}}}).by_id()
        self.assertEqual(by_id["R303"].verdict, CNE)
        self.assertTrue(any("tale" in x for x in by_id["R303"].flags), by_id["R303"].flags)

    def test_unknown_id_and_bad_verdict_ignored(self):
        r = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML,
                answers={"decisions": {"R999": {"verdict": FAIL}, "R303": {"verdict": "Approved"}}})
        self.assertEqual(r.by_id()["R303"].verdict, CNE)
        obs = " ".join(r.notes.observations)
        self.assertIn("R999", obs)
        self.assertIn("Approved", obs)

    def test_fingerprint_is_symbol_room_size_type(self):
        # PLAN section 7: fingerprint = symbol + room + size + type.
        fp = self.fp["W7"]
        for part in ("7", "107", "30.0", "36.0", "casement"):
            self.assertIn(part, fp)


class TestFacts(unittest.TestCase):
    def facts(self, **kw):
        t = {"net_clear_width_in": None, "net_clear_height_in": None, "sill_to_clear_opening_in": None,
             "source": "cut sheet", "by": "J. Doe"}
        t.update(kw)
        return {"facts": {"types": {"A": t}}}

    def test_type_A_net_clear_passes_W1_W3_R101(self):
        # 26 x 44 in = 7.94 sf >= 5.7; 26 >= 20; 44 >= 24; sill 32" + 2" = 34" <= 44".
        a = self.facts(net_clear_width_in=26, net_clear_height_in=44, sill_to_clear_opening_in=2)
        by_id = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML, answers=a).by_id()
        for fid in ("W1", "W3", "R101"):
            with self.subTest(fid):
                self.assertEqual(by_id[fid].verdict, PASS, by_id[fid].reason)
        for fid in ("W1", "W3"):
            self.assertIn("fact", by_id[fid].verdict_source)
        # Type A is also W21 in Guest Bed 303, but it is not designated: the room stays CNE.
        self.assertEqual(by_id["R303"].verdict, CNE)

    def test_room_verdict_from_fact_says_so(self):
        # A room Pass that rests on a supplied fact must not be labelled a plain rule verdict:
        # the checker needs to see that the documents alone did not decide it.
        a = self.facts(net_clear_width_in=26, net_clear_height_in=44, sill_to_clear_opening_in=2)
        r = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML, answers=a).by_id()["R101"]
        self.assertEqual(r.verdict, PASS)
        self.assertNotEqual(r.verdict_source, "rule", r.verdict_source)

    def test_fact_can_fail_a_window(self):
        # 19" wide fails 1030.2.1's 20" minimum width even though area is fine.
        a = self.facts(net_clear_width_in=19, net_clear_height_in=46, sill_to_clear_opening_in=2)
        by_id = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML, answers=a).by_id()
        self.assertEqual(by_id["W1"].verdict, FAIL, by_id["W1"].reason)
        self.assertIn("1030.2.1", by_id["W1"].code_ref)
        self.assertEqual(by_id["R101"].verdict, FAIL)

    def test_fact_area_too_small_fails(self):
        # 20 x 35 = 700 sq in = 4.86 sf < 5.0, so it fails even as a grade-floor opening.
        a = self.facts(net_clear_width_in=20, net_clear_height_in=35, sill_to_clear_opening_in=2)
        by_id = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML, answers=a).by_id()
        self.assertEqual(by_id["W1"].verdict, FAIL, by_id["W1"].reason)

    def test_fact_area_between_5_and_5_7_on_floor_1_is_cne(self):
        # 20 x 40 = 5.56 sf: under 5.7 but over the 5.0 grade-floor figure (1030.2 exception).
        # Room 101 is on the first floor, so a grade-floor opening is possible but unverified.
        a = self.facts(net_clear_width_in=20, net_clear_height_in=40, sill_to_clear_opening_in=2)
        f = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML, answers=a).by_id()["W1"]
        self.assertEqual(f.verdict, CNE, f.reason)
        self.assertIn("grade", f.reason.lower())

    def test_partial_fact_stays_cne(self):
        a = self.facts(net_clear_width_in=26)
        by_id = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML, answers=a).by_id()
        self.assertEqual(by_id["W1"].verdict, CNE)

    def test_fact_for_other_type_does_not_touch_W1(self):
        a = {"facts": {"types": {"F": {"net_clear_width_in": 26, "net_clear_height_in": 30, "sill_to_clear_opening_in": 1}}}}
        by_id = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML, answers=a).by_id()
        self.assertEqual(by_id["W1"].verdict, CNE)
        # Type F = W7 (sill 44.0 + 1 = 45 > 44) and W20 (60"): both Fail 1030.3.
        self.assertEqual(by_id["W7"].verdict, FAIL, by_id["W7"].reason)
        self.assertEqual(by_id["W20"].verdict, FAIL)

    def test_fact_sill_offset_zero_at_limit_passes_W7(self):
        # 1030.3 "not greater than 44": a clear opening bottom at exactly 44.0" complies.
        # 26 x 32 = 832 sq in = 5.78 sf >= 5.7.
        a = {"facts": {"types": {"F": {"net_clear_width_in": 26, "net_clear_height_in": 32, "sill_to_clear_opening_in": 0}}}}
        by_id = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML, answers=a).by_id()
        self.assertEqual(by_id["W7"].verdict, PASS, by_id["W7"].reason)
        self.assertEqual(by_id["R107"].verdict, PASS)

    def test_fixed_window_fails_even_with_fact(self):
        a = {"facts": {"types": {"K": {"net_clear_width_in": 40, "net_clear_height_in": 40, "sill_to_clear_opening_in": 0}}}}
        by_id = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML, answers=a).by_id()
        self.assertEqual(by_id["W13"].verdict, FAIL)


class TestTemplate(unittest.TestCase):
    def test_template_lists_open_cnes(self):
        t = template(base().findings)
        self.assertIn("A", t["facts"]["types"])
        self.assertIn("F", t["facts"]["types"])
        self.assertIn("J", t["facts"]["types"])
        self.assertIn("R303", t["decisions"])
        self.assertIn("R102", t["decisions"])
        self.assertNotIn("W10", t["decisions"])
        self.assertEqual(t["decisions"]["R303"]["fingerprint"], base().by_id()["R303"].fingerprint)

    def test_template_round_trips(self):
        t = template(base().findings)
        t = copy.deepcopy(t)
        t["decisions"]["R303"].update({"verdict": FAIL, "by": "J. Doe", "why": "x"})
        by_id = run(CODE_ANALYSIS_HTML, SCHEDULE_HTML, answers=t).by_id()
        self.assertEqual(by_id["R303"].verdict, FAIL)
        # untouched entries (verdict None) are ignored without applying
        self.assertEqual(by_id["R102"].verdict, CNE)


if __name__ == "__main__":
    unittest.main()
