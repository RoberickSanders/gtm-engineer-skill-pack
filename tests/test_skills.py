import importlib.util, os, subprocess, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from gtm.gate import read_csv, run_gated

def load(rel):
    spec = importlib.util.spec_from_file_location(rel.replace("/", "_"), os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

score = load("skills/01-map-and-score-market/score_accounts.py")
qual = load("skills/02-qualify-before-enrich/qualify.py")
wf = load("skills/03-waterfall-enrichment/waterfall.py")
mx = load("skills/05-mx-provider-split/mx_lookup.py")
ROWS = read_csv(os.path.join(ROOT, "data/sample_accounts.csv"))

class Gate(unittest.TestCase):
    def test_stops_after_ten_without_approval(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(run_gated("t", ROWS, score.process, False, d))
            self.assertEqual(len(read_csv(f"{d}/t/sample.csv")), 10)
            self.assertFalse(os.path.exists(f"{d}/t/full.csv"))
    def test_full_after_approval(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(len(run_gated("t", ROWS, score.process, True, d)), len(ROWS))

class Skills(unittest.TestCase):
    def test_score_has_reasons_and_sorted(self):
        out = score.process(ROWS)
        self.assertEqual([r["score"] for r in out], sorted((r["score"] for r in out), reverse=True))
        self.assertTrue(all(r["tier"] in "ABC" for r in out))
    def test_qualify_disqualifies(self):
        fit, _, _ = qual.classify({"website_note": "Student blog", "industry": "Media"})
        self.assertEqual(fit, "no")
        fit, c, _ = qual.classify({"website_note": "Agency managing Google Ads and Meta", "industry": "Marketing Agency"})
        self.assertEqual(fit, "yes"); self.assertGreaterEqual(c, 0.7)
    def test_waterfall_free_first_and_stops(self):
        out = wf.process(ROWS)
        for r in out:
            if r["email"]:
                self.assertTrue(r["providers_tried"].endswith(r["provider"]))
                self.assertTrue(r["email"].endswith("@" + r["domain"]))
    def test_waterfall_skips_unqualified(self):
        self.assertEqual(wf.process([{**ROWS[0], "send_to_enrichment": "no"}]), [])
    def test_mx_classify(self):
        self.assertEqual(mx.classify_mx(["aspmx.l.google.com"]), "google")
        self.assertEqual(mx.classify_mx(["x.mail.protection.outlook.com"]), "microsoft")
        self.assertEqual(mx.classify_mx(["."]), "no_mail")
        self.assertEqual(mx.classify_mx([]), "no_mail")
    def test_cli_missing_column(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("foo\n1\n")
        r = subprocess.run([sys.executable, "skills/05-mx-provider-split/mx_lookup.py", f.name], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0); self.assertIn("domain", r.stderr)

if __name__ == "__main__":
    unittest.main()
