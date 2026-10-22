"""Generate Sherpa's synthetic test fixtures. Every person, company and number here is made up.

    python tests/make_fixtures.py

Writes tests/fixtures/: four resumes (.md + .pdf), a scanned-image PDF, profile.md,
postings.jsonl (unranked) + answer-key.json, jobs.jsonl (ranked) and tracker.csv.
The counts asserted in test_scripts.py were made by hand from the tables below.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import resume_io  # noqa: E402

FX = ROOT / "tests" / "fixtures"

STRONG = """# Alex Morgan
Denver, CO | alex.morgan@example.com | (303) 555-0142 | linkedin.com/in/alexmorgan-example

## Summary
Data analyst with six years in retail and logistics analytics. I turn messy operational data into decisions that save money and time.

## Experience

### Senior Data Analyst, Ridgeway Outfitters (2022 - present)
- Cut weekly inventory write-offs by 18% ($410K a year) by building a SQL and Python demand forecast used by 42 stores
- Partnered with finance and operations leaders to set quarterly reporting priorities and presented results to the executive team each month
- Rebuilt the Tableau sales dashboard suite, reducing report requests to the analytics team from 60 to 15 a month
- Mentored two junior analysts through their first year; both were promoted

### Data Analyst, Coldwater Freight (2019 - 2022)
- Automated carrier-cost reconciliation in SQL, cutting month-end close from 9 days to 4
- Designed an on-time delivery model that flagged late-risk shipments with 81% precision
- Led a cross-team project with dispatch and billing to standardise 14 delivery status codes

### Junior Analyst, Pine Street Market (2018 - 2019)
- Built Excel and SQL reports for 6 store managers on shrink, staffing and sales
- Found a pricing error in the produce category that had cost about $2,000 a week, and worked with the category buyer to fix it

## Projects
- Open-source Snowflake cost monitor (Python, SQL): tracks warehouse spend per team and alerts on spikes; used by two local nonprofits
- Volunteer analyst for Denver Food Rescue: mapped pickup routes and cut average driver time per run from 70 to 50 minutes

## Education
BS Economics, University of Colorado Denver, 2018

## Skills
SQL (PostgreSQL, Snowflake); Python (pandas); Tableau; Excel; dbt basics; forecasting; A/B test analysis
"""

AVERAGE = """# Jordan Lee
Aurora, CO | jordan.lee@example.com | (720) 555-0199

## Experience

### Data Analyst, Brightside Insurance (2021 - present)
- Responsible for creating reports and dashboards for the claims team
- Worked with SQL and Excel to analyse claims data
- Helped improve reporting processes across the department
- Participated in a project to migrate reports to Power BI

### Operations Coordinator, Brightside Insurance (2019 - 2021)
- Coordinated schedules and maintained claims spreadsheets
- Answered questions from agents and supported the team lead

## Education
BA Business Administration, Metro State University, 2019

## Skills
SQL; Excel; Power BI; communication; teamwork
"""

WEAK = """# Sam Taylor
sam.taylor@example.com

## About Me
Hard working and passionate team player looking for oppurtunities in data. I am a fast lerner and detail orientated.

## Work
Sales Assistant, Lakeview Electronics (2020 - 2024)
- Responsible for helping customers
- Did reports sometimes

## School
Some college
"""

FLAWED_COLUMNS = """<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: letter; margin: 0.5in; }
body { font-family: Arial, sans-serif; font-size: 10pt; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 0.4in; }
</style></head><body>
<h1>Riley Chen</h1>
<div class="cols"><div>
<h2>Experience</h2>
<p>Data analyst data analyst at Summit Retail Group 2020 to 2024 where data analysis data reporting data dashboards data pipelines data quality and data governance were core to every data project I delivered.</p>
<p>Built data models for data teams, data dashboards for data consumers and data reports for data leaders across the data organisation using data tools.</p>
<p>Improved data accuracy and data timeliness for data stakeholders with data validation and data monitoring of data feeds.</p>
<p>Data analyst intern at Harbour Logistics 2019 to 2020 supporting data cleaning, data entry and data reporting for the data team.</p>
</div><div>
<h2>Skills</h2>
<p>Data analysis, data visualisation, data modelling, data engineering, data science, data storytelling, data governance, data quality.</p>
<p>SQL data querying, Python data scripting, Tableau data dashboards, Excel data workbooks, Power BI data reports.</p>
<h2>Education</h2>
<p>BS Information Systems, Front Range University, 2019, with coursework in data management and data mining.</p>
<p>Contact riley.chen@example.com or (303) 555-0177 for data opportunities.</p>
</div></div></body></html>"""

SCANNED = """<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: letter; margin: 0.5in; } body { margin: 0; }</style></head><body>
<img id="page" style="width:7.5in">
<script>
const c = document.createElement('canvas'); c.width = 1500; c.height = 1900;
const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, c.width, c.height);
g.fillStyle = '#000'; g.font = 'bold 56px Arial'; g.fillText('Casey Brooks', 60, 110);
g.font = '30px Arial';
const lines = ['casey.brooks@example.com | (303) 555-0123', '', 'EXPERIENCE',
  'Data Analyst, Mesa Health (2021 - present)', '- Built weekly SQL reports for 12 clinics',
  '- Reduced reporting errors by 30% with automated checks', '', 'EDUCATION', 'BS Statistics, 2021',
  '', 'SKILLS', 'SQL; R; Excel; Tableau'];
lines.forEach((l, i) => g.fillText(l, 60, 200 + i * 48));
document.getElementById('page').src = c.toDataURL('image/png');
</script></body></html>"""

PROFILE = """# Sherpa profile

## About you
- Name: Alex Morgan
- Email: alex.morgan@example.com
- Phone: (303) 555-0142
- City: Denver, CO
- Links: linkedin.com/in/alexmorgan-example

## Search
- Target roles: Data Analyst; Senior Data Analyst; Business Intelligence Analyst
- Seniority: mid to senior
- Location: Denver, CO
- Commute limit: 40 minutes
- Remote preference: remote or hybrid
- Salary floor: 85000 USD
- Work rights: US citizen
- Needs sponsorship: no
- Deal-breakers: gambling; tobacco
- Target industries: retail; logistics; health
- Target companies: Northwind Analytics; Copperline Energy
- Title keywords: analyst; analytics; business intelligence

## Morning brief
- Brief days: Mon;Tue;Wed;Thu;Fri
- Brief time: 08:00
- Brief length: 5
- Timezone: America/Denver

## Weekly review
- Weekly day: Fri
- Weekly time: 16:30
- Weekly application cap: 8
"""

# (company, title, location, mode, sal_min, sal_max, tier, score, likelihood, gaps, must_have, filter_reason, posted)
# Ranked against the STRONG resume. "stakeholder management" is the planted hidden strength:
# the strong resume shows it ("Partnered with finance and operations leaders...") without using the phrase.
JOBS = [
    ("Northwind Analytics", "Senior Data Analyst", "Denver, CO", "hybrid", 95000, 120000, "Apply now", 84, "strong", [], ["sql", "tableau", "python"], None, "2026-10-15"),
    ("Bluebird Health", "Data Analyst", "Remote, US", "remote", 85000, 105000, "Apply now", 80, "strong", [], ["sql", "excel"], None, "2026-10-12"),
    ("Copperline Energy", "Analytics Analyst", "Denver, CO", "onsite", 90000, 110000, "Apply now", 78, "strong", ["dbt"], ["sql", "dbt"], None, "2026-10-10"),
    ("Larkspur Retail", "Business Intelligence Analyst", "Remote, US", "remote", None, None, "Apply now", 76, "possible", ["looker"], ["sql", "looker"], None, "2026-10-08"),
    ("Fieldstone Bank", "Data Analyst II", "Denver, CO", "hybrid", 88000, 100000, "Apply now", 74, "possible", ["stakeholder management"], ["sql", "stakeholder management"], None, "2026-10-05"),
    ("Granite Logistics", "Operations Data Analyst", "Boulder, CO", "hybrid", 80000, 95000, "Apply now", 72, "possible", ["supply chain"], ["sql", "supply chain"], None, "2026-10-02"),
    ("Harbor Insurance", "Reporting Analyst", "Remote, US", "remote", 75000, 90000, "Apply now", 71, "possible", [], ["sql", "excel"], None, "2026-09-30"),
    ("Juniper Labs", "Product Analyst", "Remote, US", "remote", 100000, 125000, "Apply now", 70, "possible", ["a/b testing"], ["sql", "a/b testing"], None, "2026-09-28"),
    ("Kestrel Fintech", "Senior Analytics Engineer", "Remote, US", "remote", 130000, 150000, "Stretch", 64, "long shot", ["dbt", "airflow"], ["dbt", "airflow", "sql"], None, "2026-10-01"),
    ("Lumen Media", "Analytics Manager", "Denver, CO", "hybrid", 120000, 140000, "Stretch", 60, "long shot", ["people management"], ["people management", "sql"], None, "2026-09-25"),
    ("Maple Health", "Senior Data Analyst", "Remote, US", "remote", 105000, 125000, "Stretch", 66, "possible", ["stakeholder management"], ["sql", "stakeholder management"], None, "2026-09-22"),
    ("Nimbus Cloud", "Data Analyst", "Remote, US", "remote", None, None, "Stretch", 62, "possible", ["aws", "stakeholder management"], ["sql", "aws"], None, "2026-09-20"),
    ("Orchid Bio", "Data Scientist", "Boulder, CO", "hybrid", 115000, 135000, "Stretch", 55, "long shot", ["machine learning", "statistics"], ["machine learning", "python"], None, "2026-09-18"),
    ("Pinecrest Retail", "BI Developer", "Denver, CO", "onsite", 95000, 110000, "Stretch", 58, "possible", ["looker"], ["looker", "sql"], None, "2026-09-15"),
    ("Quarry Freight", "Senior Data Analyst", "Remote, US", "remote", 100000, 120000, "Stretch", 65, "possible", ["stakeholder management", "supply chain"], ["sql", "supply chain"], None, "2026-09-12"),
    ("Redwood County", "Data Analyst", "Denver, CO", "onsite", 80000, 90000, "Stretch", 57, "possible", ["sas"], ["sas", "sql"], None, "2026-09-10"),
    ("Summit Education", "Analytics Engineer", "Remote, US", "remote", 110000, 130000, "Stretch", 59, "long shot", ["dbt"], ["dbt", "sql"], None, "2026-09-08"),
    ("Tidewater Ads", "Marketing Analyst", "Remote, US", "remote", 70000, 85000, "Stretch", 52, "possible", ["a/b testing", "google analytics"], ["google analytics"], None, "2026-09-05"),
    ("Umber AI", "Machine Learning Engineer", "Remote, US", "remote", 150000, 190000, "Skip", 35, "long shot", ["machine learning", "pytorch"], ["pytorch", "machine learning"], None, "2026-09-03"),
    ("Vantage Capital", "Quantitative Analyst", "Denver, CO", "onsite", 140000, 170000, "Skip", 40, "long shot", ["c++", "stochastic calculus"], ["c++"], None, "2026-09-01"),
    ("Willow Health", "Director of Analytics", "Remote, US", "remote", 170000, 200000, "Skip", 38, "long shot", ["people management", "10+ years experience"], ["people management"], None, "2026-08-28"),
    ("Xenon Data", "Senior Data Engineer", "Remote, US", "remote", 140000, 160000, "Skip", 45, "long shot", ["airflow", "spark"], ["spark", "airflow"], None, "2026-08-25"),
    ("Yarrow Retail", "Data Analyst", "Remote, US", "remote", None, None, "Skip", 48, "possible", ["stakeholder management"], ["sql"], None, "2026-07-15"),
    ("Zephyr Apps", "Product Analyst", "Remote, US", "remote", 90000, 110000, "Skip", 46, "long shot", ["a/b testing", "mixpanel"], ["mixpanel"], None, "2026-08-20"),
    ("Acorn Corp", "Data Analyst", "New York, NY", "onsite", 90000, 110000, "Skip", None, "long shot", [], ["sql"], "location: onsite in New York", "2026-10-01"),
    ("Birch Defense", "Data Analyst", "Denver, CO", "onsite", 95000, 115000, "Skip", None, "long shot", ["security clearance"], ["security clearance"], "work rights: requires active security clearance", "2026-10-01"),
    ("Cedar Casino Group", "BI Analyst", "Denver, CO", "hybrid", 85000, 100000, "Skip", None, "long shot", [], ["sql"], "deal-breaker: gambling", "2026-10-01"),
    ("Dune Ltd", "Data Analyst", "London, UK", "hybrid", 50000, 60000, "Skip", None, "long shot", [], ["sql"], "work rights: UK right to work required", "2026-10-01"),
    ("Elm Staffing", "Junior Data Analyst", "Remote, US", "remote", 40000, 50000, "Skip", None, "long shot", [], ["excel"], "salary: max 50000 below floor 85000", "2026-10-01"),
    ("Fern Group", "Data Analyst", "Denver, CO", "onsite", 85000, 95000, "Skip", None, "possible", [], ["sql"], "work mode: onsite only, profile wants remote or hybrid", "2026-10-01"),
]

# (id, company, role, source, tier, likelihood, applied, stage, last_update, follow_up, history)
TRACKER = [
    ("j1", "Northwind Analytics", "Senior Data Analyst", "direct", "Apply now", "strong", "2026-09-01", "interview", "2026-09-20", "2026-10-25", "2026-09-01:applied;2026-09-08:screen;2026-09-20:interview"),
    ("j2", "Bluebird Health", "Data Analyst", "board", "Apply now", "strong", "2026-09-03", "rejected", "2026-09-17", "", "2026-09-03:applied;2026-09-17:rejected"),
    ("j3", "Copperline Energy", "Analytics Analyst", "direct", "Apply now", "strong", "2026-09-05", "screen", "2026-09-10", "2026-10-01", "2026-09-05:applied;2026-09-10:screen"),
    ("j4", "Larkspur Retail", "Business Intelligence Analyst", "board", "Apply now", "possible", "2026-09-10", "no-reply", "2026-10-10", "", "2026-09-10:applied;2026-10-10:no-reply"),
    ("j5", "Fieldstone Bank", "Data Analyst II", "direct", "Apply now", "possible", "2026-09-12", "offer", "2026-10-15", "", "2026-09-12:applied;2026-09-19:screen;2026-09-30:interview;2026-10-15:offer"),
    ("j6", "Granite Logistics", "Operations Data Analyst", "board", "Apply now", "possible", "2026-09-15", "applied", "2026-09-15", "2026-09-22", "2026-09-15:applied"),
    ("j7", "Harbor Insurance", "Reporting Analyst", "direct", "Apply now", "possible", "2026-09-20", "rejected", "2026-09-25", "", "2026-09-20:applied;2026-09-25:rejected"),
    ("j8", "Juniper Labs", "Product Analyst", "board", "Apply now", "possible", "2026-09-25", "withdrawn", "2026-10-02", "", "2026-09-25:applied;2026-10-02:withdrawn"),
    ("j9", "Kestrel Fintech", "Senior Analytics Engineer", "direct", "Stretch", "long shot", "2026-09-28", "applied", "2026-09-28", "2026-10-05", "2026-09-28:applied"),
    ("j10", "Lumen Media", "Analytics Manager", "board", "Stretch", "long shot", "2026-10-01", "rejected", "2026-10-03", "", "2026-10-01:applied;2026-10-03:rejected"),
    ("j11", "Maple Health", "Senior Data Analyst", "direct", "Stretch", "possible", "2026-10-02", "screen", "2026-10-12", "2026-10-26", "2026-10-02:applied;2026-10-12:screen"),
    ("j12", "Nimbus Cloud", "Data Analyst", "board", "Stretch", "possible", "2026-10-05", "applied", "2026-10-05", "2026-10-12", "2026-10-05:applied"),
    ("j13", "Orchid Bio", "Data Scientist", "board", "Stretch", "long shot", "2026-10-08", "no-reply", "2026-10-22", "", "2026-10-08:applied;2026-10-22:no-reply"),
    ("j14", "Pinecrest Retail", "BI Developer", "direct", "Stretch", "possible", "2026-10-10", "applied", "2026-10-10", "2026-10-17", "2026-10-10:applied"),
    ("j15", "Quarry Freight", "Senior Data Analyst", "direct", "Stretch", "possible", "2026-10-14", "rejected", "2026-10-16", "", "2026-10-14:applied;2026-10-16:rejected"),
    ("j16", "Tidewater Ads", "Marketing Analyst", "board", "Stretch", "possible", "2026-10-16", "applied", "2026-10-16", "2026-10-23", "2026-10-16:applied"),
    ("j17", "Summit Education", "Analytics Engineer", "board", "Stretch", "long shot", "2026-10-19", "applied", "2026-10-19", "2026-10-26", "2026-10-19:applied"),
    ("j18", "Ridge Analytics", "Data Analyst", "direct", "Apply now", "strong", "2026-10-20", "applied", "2026-10-20", "2026-10-27", "2026-10-20:applied"),
    ("j19", "Sable Health", "Data Analyst", "board", "Apply now", "possible", "2026-10-21", "applied", "2026-10-21", "2026-10-28", "2026-10-21:applied"),
    ("j20", "Thistle Co", "Senior Data Analyst", "direct", "Stretch", "possible", "2026-10-22", "applied", "2026-10-22", "2026-10-29", "2026-10-22:applied"),
]


def posting(i, row):
    company, title, loc, mode, smin, smax, tier, score, band, gaps, must, reason, posted = row
    desc = (f"{company} is hiring a {title} ({mode}, {loc}). Must have: {', '.join(must)}. "
            f"You will work with business teams to analyse data and report on results.")
    if company == "Yarrow Retail":  # the planted suspicious posting: old, vague, no team detail
        desc = "Exciting opportunity for a data person. Competitive pay. Apply today, start immediately."
    return {"id": f"fixture:{i:02d}", "title": title, "company": company, "location": loc, "work_mode": mode,
            "salary_min": smin, "salary_max": smax, "currency": "GBP" if "UK" in loc else "USD",
            "source": "ats" if i % 3 else "web", "url": f"https://example.com/jobs/{i:02d}",
            "apply_url": f"https://example.com/jobs/{i:02d}/apply", "posted_at": posted,
            "first_seen": "2026-10-15", "description": desc, "ats": "greenhouse" if i % 3 else None}


def main():
    FX.mkdir(parents=True, exist_ok=True)
    for name, md in (("strong", STRONG), ("average", AVERAGE), ("weak", WEAK)):
        (FX / f"resume-{name}.md").write_text(md, encoding="utf-8")
        print(name, resume_io.render(FX / f"resume-{name}.md", FX / f"resume-{name}.pdf", "letter"))
    for name, page in (("flawed-columns", FLAWED_COLUMNS), ("flawed-scanned", SCANNED)):
        print(name, resume_io.html_to_pdf(page, FX / f"resume-{name}.pdf"))
    (FX / "profile.md").write_text(PROFILE, encoding="utf-8")

    postings, ranked, key = [], [], {}
    for i, row in enumerate(JOBS, 1):
        p = posting(i, row)
        postings.append(p)
        company, title, loc, mode, smin, smax, tier, score, band, gaps, must, reason, posted = row
        key[p["id"]] = {"company": company, "tier": tier, "filter_reason": reason}
        ranked.append({**p, "must_have": must, "nice_to_have": [], "gaps": gaps, "score": score,
                       "tier": tier, "likelihood": band, "filter_reason": reason})
    write = lambda name, rows: (FX / name).write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    write("postings.jsonl", postings)
    write("jobs.jsonl", ranked)
    (FX / "answer-key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")

    cols = ["job_id", "company", "role", "source", "tier_at_apply", "likelihood_at_apply", "applied", "stage",
            "last_update", "follow_up", "history", "notes"]
    ids = {row[0]: f"fixture:{i:02d}" for i, row in enumerate(JOBS, 1)}  # link tracker rows to jobs.jsonl
    with (FX / "tracker.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in TRACKER:
            jid = ids.get(r[1]) or "manual:" + "-".join(r[1].lower().split())
            w.writerow([jid] + list(r[1:]) + [""])
    print("fixtures written to", FX)


if __name__ == "__main__":
    main()
