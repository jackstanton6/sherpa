"""Checks for Sherpa's helper scripts. Standard library only.

    python tests/make_fixtures.py      # once, or after changing fixtures
    python tests/test_scripts.py       # offline checks
    SHERPA_LIVE=1 python tests/test_scripts.py   # plus a live call to one real company per ATS
"""
import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FX = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "scripts"))
import jobs  # noqa: E402
import resume_io  # noqa: E402


def run(script, *args, stdin=None, env=None, ok=True):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *map(str, args)], input=stdin,
                       capture_output=True, text=True, encoding="utf-8", env={**os.environ, **(env or {})})
    if ok and r.returncode != 0:
        raise AssertionError(f"{script} {args} failed: {r.stdout}{r.stderr}")
    return json.loads(r.stdout)


class Home(unittest.TestCase):
    """Each test gets an empty SHERPA_HOME and a pinned 'today'."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.env = {"SHERPA_HOME": str(self.home), "SHERPA_TODAY": "2026-10-23", "SHERPA_READONLY": ""}
        os.environ.update(self.env)

    def tearDown(self):
        self.tmp.cleanup()

    def j(self, *args, **kw):
        return run("jobs.py", *args, env={**self.env, **kw.pop("env", {})}, **kw)


class Extract(unittest.TestCase):
    def codes(self, name):
        return {f["code"] for f in resume_io.extract(FX / f"resume-{name}.pdf")["flags"]}

    def test_strong_resume_is_clean(self):
        self.assertFalse(self.codes("strong") & {"no_text_layer", "suspected_columns", "keyword_stuffing",
                                                  "missing_email", "missing_phone", "missing_links"})

    def test_flawed_pdfs_are_caught(self):
        self.assertIn("suspected_columns", self.codes("flawed-columns"))
        self.assertIn("keyword_stuffing", self.codes("flawed-columns"))
        self.assertIn("no_text_layer", self.codes("flawed-scanned"))

    def test_weak_resume_flags(self):
        self.assertTrue({"missing_phone", "missing_links", "nonstandard_headings", "too_short"} <= self.codes("weak"))

    def test_markdown_and_docx_inputs(self):
        self.assertIn("Alex Morgan", resume_io.extract(FX / "resume-strong.md")["text"])


class RoundTrip(unittest.TestCase):
    def test_render_then_extract_gives_same_words(self):
        with tempfile.TemporaryDirectory() as td:
            res = resume_io.render(FX / "resume-strong.md", Path(td) / "out.pdf", "letter")
            if not res["ok"]:
                self.skipTest("no PDF renderer installed")
            words = lambda s: re.findall(r"[a-z0-9$%]+", resume_io.norm(s))
            md = re.sub(r"^\s*(#+|[-*])\s+", "", (FX / "resume-strong.md").read_text(encoding="utf-8"), flags=re.M)
            back = resume_io.extract(res["out"])
            self.assertEqual(words(md), words(back["text"]))
            self.assertNotIn("suspected_columns", {f["code"] for f in back["flags"]})


class Quotes(unittest.TestCase):
    def test_real_quotes_match_and_invented_ones_do_not(self):
        panel = {"reviewer": "recruiter", "strongest": [
            {"quote": "Cut weekly inventory write-offs by 18% ($410K a year)", "why": "x"},
            {"quote": "Automated carrier‑cost  reconciliation in SQL,\ncutting month-end close", "why": "x"}],
            "weakest": [{"quote": "Led a team of 12 engineers at Google", "why": "invented"}],
            "fixes": [{"before": "Mentored two junior analysts through their first year", "after": "..."}]}
        with tempfile.TemporaryDirectory() as td:
            q = Path(td) / "q.json"
            q.write_text(json.dumps([panel]), encoding="utf-8")
            res = run("resume_io.py", "verify-quotes", FX / "resume-strong.md", q, ok=False)
        self.assertEqual(res["unmatched"], ["Led a team of 12 engineers at Google"])
        self.assertEqual(len(res["matched"]), 3)
        self.assertFalse(res["ok"])

    def test_quotes_against_pdf(self):
        with tempfile.TemporaryDirectory() as td:
            q = Path(td) / "q.json"
            q.write_text(json.dumps(["Rebuilt the Tableau sales dashboard suite"]), encoding="utf-8")
            self.assertTrue(run("resume_io.py", "verify-quotes", FX / "resume-strong.pdf", q)["ok"])


class Gaps(Home):
    def test_counts_match_hand_count(self):
        r = self.j("gaps", "--jobs", FX / "jobs.jsonl")
        g = {x["gap"]: x for x in r["gaps"]}
        self.assertEqual(r["jobs_scored"], 30)
        self.assertEqual(r["near_miss_jobs"], 16)  # 10 Stretch + 6 Skip on fit
        sm = g["stakeholder management"]
        self.assertEqual((sm["total"], sm["near_miss"], sm["unlock"], sm["only_gap"]), (5, 4, 3, 2))
        self.assertEqual(sm["by_tier"], {"Apply now": 1, "Stretch": 3, "Skip": 1})
        self.assertEqual((g["dbt"]["total"], g["dbt"]["unlock"], g["dbt"]["only_gap"]), (3, 2, 1))
        self.assertEqual((g["a/b testing"]["total"], g["a/b testing"]["unlock"]), (3, 2))
        self.assertEqual((g["airflow"]["total"], g["airflow"]["unlock"]), (2, 1))
        self.assertEqual(g["security clearance"]["near_miss"], 0)  # hard-filter skip, not a near miss
        self.assertEqual(r["gaps"][0]["gap"], "stakeholder management")


class Stats(Home):
    def test_figures_match_hand_count(self):
        s = self.j("stats", FX / "tracker.csv")
        self.assertEqual(s["week"], "2026-W43")
        self.assertEqual((s["total"]["n"], s["total"]["replied"], s["total"]["interviews"]), (20, 8, 2))
        self.assertEqual(s["total"]["reply_rate"], 0.4)
        self.assertEqual(s["this_week"]["applications"], 4)
        self.assertEqual(s["by_stage"], {"applied": 9, "screen": 2, "interview": 1, "offer": 1,
                                         "rejected": 4, "withdrawn": 1, "no-reply": 2})
        self.assertEqual((s["by_source"]["direct"]["n"], s["by_source"]["direct"]["replied"]), (10, 6))
        self.assertEqual((s["by_source"]["board"]["n"], s["by_source"]["board"]["replied"]), (10, 2))
        self.assertEqual(s["days_to_reply"], {"n": 8, "median": 6.0})
        self.assertEqual(s["overdue_followups"]["n"], 6)
        self.assertEqual(s["stale_14_days"]["n"], 5)
        self.assertTrue(s["by_likelihood"]["strong"]["too_early"])  # n=4 < 5
        self.assertFalse(s["by_tier"]["Apply now"]["too_early"])

    def test_small_sample_is_too_early(self):
        p = self.home / "small.csv"
        lines = (FX / "tracker.csv").read_text(encoding="utf-8").splitlines()[:4]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        s = self.j("stats", p)
        self.assertEqual(s["total"]["n"], 3)
        self.assertTrue(s["total"]["too_early"])


class JobFlow(Home):
    def test_dedupe_prefers_company_feed(self):
        board = {"title": "Data Analyst", "company": "Acme", "location": "Denver, CO", "source": "web",
                 "url": "https://board.example/1", "first_seen": "2026-10-01"}
        feed = {**board, "source": "ats", "url": "https://acme.example/jobs/1", "first_seen": "2026-10-05"}
        r = self.j("dedupe", stdin=json.dumps([board, feed]))
        self.assertEqual((r["before"], r["after"]), (2, 1))
        job = r["jobs"][0]
        self.assertEqual((job["source"], job["first_seen"]), ("ats", "2026-10-01"))
        self.assertEqual(job["also_on"], ["https://board.example/1"])

    def test_seen_reports_only_new_then_nothing_then_changes(self):
        postings = (FX / "postings.jsonl").read_text(encoding="utf-8")
        self.assertEqual(len(self.j("seen", stdin=postings)["new"]), 30)
        second = self.j("seen", stdin=postings)
        self.assertEqual((len(second["new"]), len(second["changed"])), (0, 0))
        rows = [json.loads(l) for l in postings.splitlines()]
        rows[0]["description"] += " Now offering a signing bonus."
        third = self.j("seen", stdin="\n".join(map(json.dumps, rows)))
        self.assertEqual([c["id"] for c in third["changed"]], ["fixture:01"])

    def test_seen_accepts_compact_lists(self):
        compact = self.j("normalize", stdin=(FX / "postings.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(len(self.j("seen", stdin=json.dumps(compact))["new"]), 30)
        again = self.j("seen", stdin=json.dumps(compact))  # snippets must not look like changes
        self.assertEqual((len(again["new"]), len(again["changed"])), (0, 0))

    def test_save_validates_and_normalises_gaps(self):
        self.j("normalize", stdin=(FX / "postings.jsonl").read_text(encoding="utf-8"))
        bad = self.j("save", stdin=json.dumps([{"id": "fixture:01", "tier": "Maybe", "likelihood": "strong"}]), ok=False)
        self.assertFalse(bad["ok"])
        good = self.j("save", stdin=json.dumps([{"id": "fixture:01", "tier": "Apply now", "likelihood": "strong",
                                                 "score": 81, "gaps": ["  SQL ", "People  Management"]}]))
        self.assertEqual(good["saved"], 1)
        shown = self.j("show", "fixture:01")["jobs"][0]
        self.assertEqual(shown["gaps"], ["sql", "people management"])
        self.assertEqual(shown["company"], "Northwind Analytics")

    def test_tracker_add_update_and_readonly(self):
        (self.home / "jobs.jsonl").write_text((FX / "jobs.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
        row = self.j("track", "add", "--job-id", "fixture:01")["row"]
        self.assertEqual((row["company"], row["source"], row["tier_at_apply"], row["follow_up"]),
                         ("Northwind Analytics", "direct", "Apply now", "2026-10-30"))
        row = self.j("track", "update", "fixture:01", "--stage", "screen", "--date", "2026-10-25")["row"]
        self.assertEqual(row["history"], "2026-10-23:applied;2026-10-25:screen")
        blocked = self.j("track", "update", "fixture:01", "--stage", "offer", env={"SHERPA_READONLY": "1"}, ok=False)
        self.assertIn("Read-only", blocked["error"])
        with (self.home / "tracker.csv").open(encoding="utf-8") as f:
            self.assertEqual(list(csv.DictReader(f))[0]["stage"], "screen")

    def test_status_and_profile_parsing(self):
        self.assertEqual(self.j("status")["next"], "Run /sherpa:setup first.")
        (self.home / "profile.md").write_text((FX / "profile.md").read_text(encoding="utf-8"), encoding="utf-8")
        (self.home / "resume-master.md").write_text("x", encoding="utf-8")
        s = self.j("status")
        self.assertTrue(s["ready"])
        self.assertEqual(s["profile"]["salary floor"], "85000 USD")

    def test_schedule_writes_readonly_wrapper_without_installing(self):
        (self.home / "profile.md").write_text((FX / "profile.md").read_text(encoding="utf-8"), encoding="utf-8")
        r = self.j("schedule", "morning")
        self.assertFalse(r["installed"])
        self.assertEqual((r["days"], r["time"]), (["Mon", "Tue", "Wed", "Thu", "Fri"], "08:00"))
        script = Path(r["script"]).read_text(encoding="utf-8")
        self.assertIn("SHERPA_READONLY=1", script)
        self.assertIn("Edit(./briefs/**)", script)
        self.assertIn("/sherpa:morning scheduled", script)
        self.assertNotIn("Edit", r["denied_tools"])  # a deny would override the briefs/ allow

    def test_upstream_errors_are_not_recorded_as_jobs(self):
        err = json.dumps({"ok": False, "error": "Adzuna is optional and not configured."})
        r = self.j("seen", stdin=err, ok=False)
        self.assertIn("not configured", r["error"])
        self.assertFalse((self.home / "jobs.jsonl").exists())

    def test_inline_json_argument(self):
        self.j("normalize", (FX / "postings.jsonl").read_text(encoding="utf-8").splitlines()[0])
        r = self.j("save", '[{"id": "fixture:01", "tier": "Stretch", "likelihood": "possible", "score": 60}]')
        self.assertEqual(r["saved"], 1)


class Adapters(Home):
    """Each ATS adapter maps its own payload shape. Canned payloads, no network."""
    CANNED = {
        "greenhouse": {"jobs": [{"id": 1, "title": "Data Analyst", "company_name": "Acme", "location": {"name": "Remote - US"},
                                 "absolute_url": "https://acme.example/j/1", "first_published": "2026-10-01T10:00:00-04:00",
                                 "content": "&lt;p&gt;Use &lt;b&gt;SQL&lt;/b&gt; daily&lt;/p&gt;"}]},
        "lever": [{"id": "abc", "text": "Data Analyst", "categories": {"location": "Denver"}, "workplaceType": "hybrid",
                   "salaryRange": {"min": 90000, "max": 110000, "currency": "USD"}, "hostedUrl": "https://l.example/abc",
                   "applyUrl": "https://l.example/abc/apply", "createdAt": 1790000000000, "descriptionPlain": "Use SQL daily"}],
        "ashby": {"jobs": [{"id": "x1", "title": "Data Analyst", "location": "NYC", "workplaceType": "OnSite",
                            "jobUrl": "https://a.example/x1", "applyUrl": "https://a.example/x1/application",
                            "publishedAt": "2026-10-02T00:00:00Z", "descriptionPlain": "Use SQL daily",
                            "compensation": {"summaryComponents": [{"compensationType": "Salary", "minValue": 1, "maxValue": 2, "currencyCode": "USD"}]}}]},
        "workable": {"name": "Acme", "jobs": [{"shortcode": "S1", "title": "Data Analyst", "telecommuting": True,
                                               "city": "Paris", "country": "France", "url": "https://w.example/S1",
                                               "application_url": "https://w.example/S1/apply", "published_on": "2026-10-03",
                                               "description": "<p>Use SQL daily</p>"}]},
    }

    def test_each_adapter_normalises(self):
        modes = {"greenhouse": "remote", "lever": "hybrid", "ashby": "onsite", "workable": "remote"}
        for ats, payload in self.CANNED.items():
            jobs.fetch = lambda url, as_json=True, ttl=0, p=payload: (200, p)
            got = jobs.ADAPTERS[ats]("acme", "Acme")
            self.assertEqual(len(got), 1, ats)
            j = got[0]
            self.assertEqual((j["title"], j["source"], j["work_mode"]), ("Data Analyst", "ats", modes[ats]), ats)
            self.assertTrue(j["id"].startswith(f"{ats}:acme:"), ats)
            self.assertIn("SQL", j["description"], ats)
            self.assertNotIn("<", j["description"], ats)
            self.assertRegex(j["posted_at"], r"^\d{4}-\d{2}-\d{2}$", ats)

    def test_not_found_is_none(self):
        jobs.fetch = lambda url, as_json=True, ttl=0: (404, "")
        for fn in jobs.ADAPTERS.values():
            self.assertIsNone(fn("nope", "Nope"))

    def test_detect_from_urls_and_pages(self):
        self.assertEqual(jobs.detect("https://boards.greenhouse.io/stripe"), ("greenhouse", "stripe"))
        self.assertEqual(jobs.detect('<iframe src="https://boards.greenhouse.io/embed/job_board?for=figma">'), ("greenhouse", "figma"))
        self.assertEqual(jobs.detect("https://jobs.lever.co/palantir/123"), ("lever", "palantir"))
        self.assertEqual(jobs.detect("https://jobs.ashbyhq.com/openai"), ("ashby", "openai"))
        self.assertEqual(jobs.detect("https://apply.workable.com/huggingface/"), ("workable", "huggingface"))
        self.assertEqual(jobs.detect("https://example.com/careers"), (None, None))


@unittest.skipUnless(os.environ.get("SHERPA_LIVE") == "1", "set SHERPA_LIVE=1 for live ATS calls")
class Live(Home):
    def test_one_real_company_per_ats(self):
        for url in ("https://boards.greenhouse.io/stripe", "https://jobs.lever.co/palantir",
                    "https://jobs.ashbyhq.com/openai", "https://apply.workable.com/huggingface/"):
            with self.subTest(url=url):
                r = self.j("probe", url, "--match", "engineer", "--max", "1")
                self.assertEqual(r["coverage"][0]["status"], "ok")
                self.assertGreater(r["coverage"][0]["jobs_total"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
