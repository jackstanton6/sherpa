#!/usr/bin/env python3
"""Sherpa job helper. Python standard library only. Every command prints JSON.

Data lives in $SHERPA_HOME (default ~/.sherpa). Set SHERPA_TODAY=YYYY-MM-DD to pin "today".
SHERPA_READONLY=1 (set by scheduled runs) blocks commands that change the tracker,
watchlist membership or schedules.

  status                                  what exists, parsed profile, what's missing
  probe <careers-url-or-company> [--match "a;b"] [--company NAME] [--max 60]
  probe --watchlist [--limit 30] [--match "a;b"] [--max 60]
  watch add <name> [--url URL] | watch list
  api adzuna --query Q --where W [--country us]
  normalize [file]       jobs found elsewhere (web search) -> schema, stored in the inbox
  dedupe [file]          merge duplicates in a job list
  seen [file] [--dry-run]  keep only jobs new or changed vs jobs.jsonl, then record them
  show <id> [<id> ...]   full job records (with description)
  save [file]            upsert ranked jobs into jobs.jsonl
  gaps                   gap phrase counts and unlock counts from jobs.jsonl
  pay <keywords>         salary ranges seen in jobs.jsonl for matching titles
  stats [tracker.csv] [--min-sample 5]
  track add --job-id ID [--applied D] [--follow-up D] [--note N] [--company C --role R --source S]
  track update <job_id> --stage S [--date D] [--follow-up D] [--note N]
  track list
  schedule morning|weekly [--install|--remove] [--plugin-dir DIR]

[file] arguments may be a path, inline JSON ('[{...}]'), or omitted for stdin.
Lists may be a JSON array, JSONL, or {"jobs": [...]}.
"""
import argparse
import csv
import hashlib
import html
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

UA = "sherpa-jobs/0.3 (+https://github.com/jackstanton6/sherpa; personal job search)"
STAGES = ["applied", "screen", "interview", "offer", "rejected", "withdrawn", "no-reply"]
ACTIVE = {"applied", "screen", "interview"}
REPLIED = {"screen", "interview", "offer", "rejected"}
TIERS = ["Apply now", "Stretch", "Skip"]
BANDS = ["strong", "possible", "long shot"]
TRACKER_COLS = ["job_id", "company", "role", "source", "tier_at_apply", "likelihood_at_apply", "applied",
                "stage", "last_update", "follow_up", "history", "notes"]
FIELDS = ["id", "title", "company", "location", "work_mode", "salary_min", "salary_max", "currency", "source",
          "url", "apply_url", "posted_at", "first_seen", "description", "ats"]
RANK_FIELDS = ["must_have", "nice_to_have", "gaps", "score", "tier", "likelihood", "filter_reason",
               "reasons", "legitimacy"]


# ---------------------------------------------------------------- basics

def home():
    h = Path(os.environ.get("SHERPA_HOME") or Path.home() / ".sherpa")
    h.mkdir(parents=True, exist_ok=True)
    return h


def today():
    return date.fromisoformat(os.environ["SHERPA_TODAY"]) if os.environ.get("SHERPA_TODAY") else date.today()


def emit(obj, code=0):
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))
    sys.exit(code)


def fail(msg, **extra):
    emit({"ok": False, "error": msg, **extra}, 2)


def guard_write(what):
    if os.environ.get("SHERPA_READONLY") == "1":
        fail(f"Read-only run: '{what}' is not allowed in a scheduled run.")


def read_jsonl(path):
    if not Path(path).exists():
        return []
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path, rows):
    tmp = Path(str(path) + ".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(path)


def load(src):
    """JSON or JSONL from inline JSON, a file path, or stdin. Inline JSON lets scheduled runs, whose
    permissions only match single-line `python ...` commands, pass data without heredocs or temp files."""
    if src and src.lstrip()[:1] in ("[", "{"):
        raw = src.strip()
    else:
        raw = (Path(src).read_text(encoding="utf-8") if src and src != "-" else sys.stdin.read()).strip()
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return [json.loads(l) for l in raw.splitlines() if l.strip()]


def jobs_of(data):
    """A job list from a JSON array, JSONL, or an object with a "jobs" key (e.g. probe output).
    An upstream error object ({"ok": false, ...}) piped in stops here instead of becoming a blank job."""
    if isinstance(data, dict):
        if data.get("ok") is False:
            fail(f"Input was an error, not jobs: {data.get('error')}", upstream=data)
        return data.get("jobs", [data] if data.get("title") else [])
    return data


def read_list(src):
    return jobs_of(load(src))


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


def key(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def to_date(v):
    """ISO date string from ISO strings, ms epochs or None."""
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit()):
        return datetime.fromtimestamp(int(v) / 1000, tz=timezone.utc).date().isoformat()
    m = re.match(r"\d{4}-\d{2}-\d{2}", str(v))
    return m.group(0) if m else None


def clean_html(s):
    s = html.unescape(s or "")
    s = re.sub(r"<(br|/p|/li|/h\d|/div)[^>]*>", "\n", s, flags=re.I)
    s = re.sub(r"<li[^>]*>", "- ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t ]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s).strip()


def work_mode(*texts):
    t = " ".join(str(x) for x in texts if x).lower()
    if "hybrid" in t:
        return "hybrid"
    if "remote" in t or "telecommut" in t:
        return "remote"
    if "onsite" in t or "on-site" in t or "in office" in t or "in-office" in t:
        return "onsite"
    return "unknown"


def norm_job(d):
    """Fill the Sherpa schema, assign a stable id and a content hash."""
    j = {f: d.get(f) for f in FIELDS}
    j.update({k: d[k] for k in RANK_FIELDS + ["also_on"] if k in d})
    j["source"] = j["source"] if j["source"] in ("ats", "api", "web") else "web"
    j["work_mode"] = j["work_mode"] if j["work_mode"] in ("onsite", "hybrid", "remote") else \
        work_mode(j["location"], j["title"])
    j["description"] = clean_html(j["description"])[:8000]
    j["posted_at"] = to_date(j["posted_at"])
    j["first_seen"] = to_date(j["first_seen"]) or today().isoformat()
    j["apply_url"] = j["apply_url"] or j["url"]
    for k in ("salary_min", "salary_max"):
        try:
            j[k] = int(float(j[k])) if j[k] not in (None, "") else None
        except (TypeError, ValueError):
            j[k] = None
    if not j["id"]:
        basis = "|".join(key(j[k]) for k in ("company", "title", "location")) + "|" + (j["url"] or "")
        j["id"] = f"{j['source']}:{hashlib.sha1(basis.encode()).hexdigest()[:12]}"
    j["hash"] = hashlib.sha1(json.dumps([j["title"], j["description"], j["salary_min"], j["salary_max"]])
                             .encode()).hexdigest()[:12]
    return j


def compact(j):
    """What Claude sees in lists. Full text comes from `show`."""
    c = {k: j.get(k) for k in ("id", "title", "company", "location", "work_mode", "salary_min", "salary_max",
                               "currency", "posted_at", "source", "ats", "url")}
    c["snippet"] = (j.get("description") or "")[:240]
    return c


# ---------------------------------------------------------------- polite HTTP

_last_hit = {}
_robots = {}


def fetch(url, as_json=True, ttl=3600):
    """GET with a clear User-Agent, 1 req/sec per host, and a one-hour disk cache.
    Returns (status, body). Network errors return status 0."""
    cache = home() / "cache" / (hashlib.sha1(url.encode()).hexdigest() + ".json")
    if cache.exists() and time.time() - cache.stat().st_mtime < ttl:
        c = json.loads(cache.read_text(encoding="utf-8"))
        return c["status"], c["body"]
    host = urllib.parse.urlparse(url).netloc
    wait = 1.0 - (time.time() - _last_hit.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    _last_hit[host] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, text/html"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            status, text = r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        status, text = e.code, ""
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return 0, str(e)
    body = text
    if as_json and status == 200:
        try:
            body = json.loads(text)
        except json.JSONDecodeError:
            status = 0
    if status in (200, 404):
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(json.dumps({"status": status, "body": body}), encoding="utf-8")
    return status, body


def robots_ok(url):
    p = urllib.parse.urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
        try:
            rp.read()
        except Exception:
            rp = None  # unreadable robots.txt: treat as allowed
        _robots[base] = rp
    rp = _robots[base]
    return rp is None or rp.can_fetch(UA, url)


# ---------------------------------------------------------------- ATS adapters
# One small function per ATS so one breaking doesn't affect the rest.
# Each returns a list of normalised jobs, or None when the board doesn't exist.

def greenhouse(slug, company):
    st, body = fetch(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
    if st != 200:
        return None
    return [norm_job({
        "id": f"greenhouse:{slug}:{j['id']}", "title": j.get("title"),
        "company": j.get("company_name") or company, "location": (j.get("location") or {}).get("name"),
        "source": "ats", "ats": "greenhouse", "url": j.get("absolute_url"), "apply_url": j.get("absolute_url"),
        "posted_at": j.get("first_published") or j.get("updated_at"), "description": j.get("content"),
    }) for j in body.get("jobs", [])]


def lever(slug, company):
    st, body = fetch(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    if st != 200 or not isinstance(body, list):
        return None
    jobs = []
    for j in body:
        cat, sal = j.get("categories") or {}, j.get("salaryRange") or {}
        jobs.append(norm_job({
            "id": f"lever:{slug}:{j['id']}", "title": j.get("text"), "company": company,
            "location": cat.get("location"), "work_mode": j.get("workplaceType"),
            "salary_min": sal.get("min"), "salary_max": sal.get("max"), "currency": sal.get("currency"),
            "source": "ats", "ats": "lever", "url": j.get("hostedUrl"), "apply_url": j.get("applyUrl"),
            "posted_at": j.get("createdAt"),
            "description": "\n".join(x for x in (j.get("descriptionPlain"), j.get("additionalPlain")) if x),
        }))
    return jobs


def ashby(slug, company):
    st, body = fetch(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true")
    if st != 200:
        return None
    jobs = []
    for j in body.get("jobs", []):
        if j.get("isListed") is False:
            continue
        sal = next((c for c in ((j.get("compensation") or {}).get("summaryComponents") or [])
                    if c.get("compensationType") == "Salary"), {})
        mode = (j.get("workplaceType") or "").lower() or ("remote" if j.get("isRemote") else None)
        jobs.append(norm_job({
            "id": f"ashby:{slug}:{j['id']}", "title": j.get("title"), "company": company,
            "location": j.get("location"), "work_mode": mode,
            "salary_min": sal.get("minValue"), "salary_max": sal.get("maxValue"), "currency": sal.get("currencyCode"),
            "source": "ats", "ats": "ashby", "url": j.get("jobUrl"), "apply_url": j.get("applyUrl"),
            "posted_at": j.get("publishedAt"), "description": j.get("descriptionPlain") or j.get("descriptionHtml"),
        }))
    return jobs


def workable(slug, company):
    st, body = fetch(f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true")
    if st != 200:
        return None
    return [norm_job({
        "id": f"workable:{slug}:{j.get('shortcode')}", "title": j.get("title"),
        "company": body.get("name") or company,
        "location": ", ".join(x for x in (j.get("city"), j.get("state"), j.get("country")) if x),
        "work_mode": "remote" if j.get("telecommuting") else None,
        "source": "ats", "ats": "workable", "url": j.get("url"), "apply_url": j.get("application_url"),
        "posted_at": j.get("published_on") or j.get("created_at"), "description": j.get("description"),
    }) for j in body.get("jobs", [])]


ADAPTERS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby, "workable": workable}
PATTERNS = [
    ("greenhouse", r"(?:boards|job-boards)(?:-api)?\.greenhouse\.io/(?:v1/boards/|embed/job_board(?:/js)?\?for=)?([A-Za-z0-9_-]+)"),
    ("greenhouse", r"greenhouse\.io/embed/job_board(?:/js)?\?for=([A-Za-z0-9_-]+)"),
    ("lever", r"jobs\.lever\.co/([A-Za-z0-9_-]+)"),
    ("lever", r"api\.lever\.co/v0/postings/([A-Za-z0-9_-]+)"),
    ("ashby", r"jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]+)"),
    ("ashby", r"posting-api/job-board/([A-Za-z0-9_.%-]+)"),
    ("workable", r"apply\.workable\.com/(?!api|j/)([A-Za-z0-9_-]+)"),
    ("workable", r"//([A-Za-z0-9_-]+)\.workable\.com"),
]
NOT_SLUGS = {"embed", "v1", "boards", "jobs", "www", "apply", "careers", "api"}


def detect(text):
    for ats, pat in PATTERNS:
        for m in re.finditer(pat, text):
            slug = m.group(1)
            if slug.lower() not in NOT_SLUGS:
                return ats, slug
    return None, None


def resolve(name, url):
    """Find (ats, slug, how) for a company: URL pattern, then page markers, then slug guesses."""
    if url:
        ats, slug = detect(url)
        if ats:
            return ats, slug, "url"
        if not robots_ok(url):
            return None, None, "blocked"
        st, page = fetch(url, as_json=False)
        if st == 200:
            ats, slug = detect(page)
            if ats:
                return ats, slug, "page"
        elif st == 0 or st >= 400:
            return None, None, "unreachable"
    for slug in dict.fromkeys([re.sub(r"[^a-z0-9]", "", (name or "").lower()), slugify(name)]):
        if not slug:
            continue
        for ats, fn in ADAPTERS.items():
            if fn(slug, name) is not None:
                return ats, slug, "guessed"
    return None, None, "no-feed"


def keywords(match):
    if match:
        return [k.strip().lower() for k in match.split(";") if k.strip()]
    p = profile()
    kws = split(p.get("title keywords")) or split(p.get("target roles"))
    return [k.lower() for k in kws]


def title_ok(job, kws):
    return not kws or any(k in (job.get("title") or "").lower() for k in kws)


def probe_one(name, url, ats=None, slug=None, kws=()):
    how = "known"
    if not (ats and slug):
        ats, slug, how = resolve(name, url)
    if not ats:
        return [], {"company": name, "status": how, "careers_url": url}
    jobs = ADAPTERS[ats](slug, name)
    if jobs is None:
        return [], {"company": name, "status": "unreachable", "ats": ats, "slug": slug,
                    "detail": "feed returned an error; the slug may have changed"}
    matched = [j for j in jobs if title_ok(j, kws)]
    return matched, {"company": name, "status": "ok", "ats": ats, "slug": slug, "found_by": how,
                     "jobs_total": len(jobs), "jobs_matched": len(matched)}


def inbox_add(jobs):
    """Keep full records in inbox.jsonl (30 days) so lists can stay compact."""
    path = home() / "inbox.jsonl"
    cutoff = (today() - timedelta(days=30)).isoformat()
    rows = {r["id"]: r for r in read_jsonl(path) if (r.get("first_seen") or "") >= cutoff}
    for j in jobs:
        rows[j["id"]] = {**rows.get(j["id"], {}), **j}
    write_jsonl(path, list(rows.values()))


def cmd_probe(a):
    kws = keywords(a.match)
    if a.watchlist:
        wl = watchlist()
        if not wl:
            fail("Watchlist is empty. Add companies with `watch add` first.")
        todo = sorted(wl, key=lambda w: w.get("last_checked") or "")[:a.limit]
        jobs, coverage = [], []
        for w in todo:
            found, cov = probe_one(w["name"], w.get("careers_url"), w.get("ats"), w.get("slug"), kws)
            jobs += found
            coverage.append(cov)
            w.update({"last_checked": today().isoformat(), "status": cov["status"]})
            if cov.get("ats"):
                w.update({"ats": cov["ats"], "slug": cov["slug"], "guessed": cov.get("found_by") == "guessed"
                          or w.get("guessed", False)})
        save_watchlist(wl)
        skipped = len(wl) - len(todo)
    else:
        target = a.target or fail("Give a careers URL or company name, or use --watchlist.")
        is_url = target.startswith("http")
        name = a.company or target
        if is_url and not a.company:
            slug = detect(target)[1]
            host = urllib.parse.urlparse(target).netloc.removeprefix("www.").removeprefix("careers.")
            name = (slug or host.split(".")[0]).replace("-", " ").title()
        jobs, cov = probe_one(name, target if is_url else None, kws=kws)
        coverage, skipped = [cov], 0
    jobs = dedupe(jobs)
    inbox_add(jobs)
    jobs.sort(key=lambda j: j.get("posted_at") or "", reverse=True)
    emit({"ok": True, "match": kws, "jobs": [compact(j) for j in jobs[:a.max]], "coverage": coverage,
          "more_matched": max(0, len(jobs) - a.max), "not_checked_this_run": skipped,
          "note": "All matches are stored in the inbox; narrow --match to see others." if len(jobs) > a.max else None})


# ---------------------------------------------------------------- watchlist

def watchlist():
    p = home() / "watchlist.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def save_watchlist(wl):
    (home() / "watchlist.json").write_text(json.dumps(wl, indent=2, ensure_ascii=False), encoding="utf-8")


def cmd_watch(a):
    wl = watchlist()
    if a.action == "list":
        stale = (today() - timedelta(days=14)).isoformat()
        emit({"ok": True, "count": len(wl), "companies": wl,
              "broken": [w["name"] for w in wl if w.get("status") in ("unreachable", "blocked")],
              "not_checked_14_days": [w["name"] for w in wl if (w.get("last_checked") or "") < stale]})
    guard_write("watch add")
    if not a.name:
        fail("watch add needs a company name.")
    existing = next((w for w in wl if key(w["name"]) == key(a.name)), None)
    if existing:
        if a.url:
            existing.update({"careers_url": a.url, "ats": None, "slug": None})
    else:
        ats, slug = detect(a.url or "")
        wl.append({"name": a.name, "careers_url": a.url, "ats": ats, "slug": slug,
                   "last_checked": None, "status": "new"})
    save_watchlist(wl)
    emit({"ok": True, "count": len(wl), "added": not existing, "name": a.name})


# ---------------------------------------------------------------- job APIs

def cmd_api(a):
    if a.name != "adzuna":
        fail(f"Unknown API '{a.name}'. Available: adzuna.")
    app_id, app_key = os.environ.get("ADZUNA_APP_ID"), os.environ.get("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        fail("Adzuna is optional and not configured. Set ADZUNA_APP_ID and ADZUNA_APP_KEY "
             "(free at developer.adzuna.com).", configured=False)
    country = a.country or os.environ.get("ADZUNA_COUNTRY", "us")
    q = urllib.parse.urlencode({"app_id": app_id, "app_key": app_key, "what": a.query, "where": a.where or "",
                                "results_per_page": 50, "content-type": "application/json"})
    st, body = fetch(f"https://api.adzuna.com/v1/api/jobs/{country}/search/1?{q}")
    if st != 200:
        fail(f"Adzuna returned status {st}.")
    jobs = dedupe([norm_job({
        "id": f"adzuna:{r.get('id')}", "title": r.get("title"),
        "company": (r.get("company") or {}).get("display_name"),
        "location": (r.get("location") or {}).get("display_name"),
        "salary_min": r.get("salary_min"), "salary_max": r.get("salary_max"),
        "currency": {"gb": "GBP", "us": "USD", "au": "AUD", "ca": "CAD", "nz": "NZD"}.get(country),
        "source": "api", "url": r.get("redirect_url"), "posted_at": r.get("created"),
        "description": r.get("description"),
    }) for r in body.get("results", [])])
    inbox_add(jobs)
    emit({"ok": True, "jobs": [compact(j) for j in jobs], "count": len(jobs)})


# ---------------------------------------------------------------- dedupe / seen / show / save

def dedupe(jobs):
    """Merge on URL, or on company + title + location. Prefer the company's own feed, keep the earliest
    first_seen, and remember the other places the job appeared (a board-only listing is a signal)."""
    out, by_key, by_url = [], {}, {}
    rank = {"ats": 0, "api": 1, "web": 2}
    for j in (norm_job(x) for x in jobs):
        k = (key(j["company"]), key(j["title"]), key(j["location"]))
        prev = by_url.get(j["url"]) if j["url"] else None
        prev = prev or by_key.get(k)
        if prev is None:
            out.append(j)
            by_key[k] = j
            if j["url"]:
                by_url[j["url"]] = j
            continue
        keep, other = (j, prev) if rank[j["source"]] < rank[prev["source"]] else (prev, j)
        merged = {**other, **keep}
        merged["first_seen"] = min(prev["first_seen"], j["first_seen"])
        merged["also_on"] = sorted({*(prev.get("also_on") or []), *(j.get("also_on") or []), other["url"]}
                                   - {keep["url"], None})
        prev.clear()
        prev.update(merged)
        by_key[k] = prev
        if j["url"]:
            by_url[j["url"]] = prev
    return out


def jobs_path():
    return home() / "jobs.jsonl"


def cmd_normalize(a):
    jobs = dedupe(read_list(a.file))
    inbox_add(jobs)
    emit({"ok": True, "jobs": [compact(j) for j in jobs], "count": len(jobs)})


def cmd_dedupe(a):
    jobs = read_list(a.file)
    merged = dedupe(jobs)
    emit({"ok": True, "before": len(jobs), "after": len(merged), "jobs": merged})


def cmd_seen(a):
    data = load(a.file)
    inbox = {j["id"]: j for j in read_jsonl(home() / "inbox.jsonl")}
    raw = [{**inbox.get(x.get("id"), {}), **x} for x in jobs_of(data)]  # compact lists -> full records
    known = {j["id"]: j for j in read_jsonl(jobs_path())}
    known_keys = {(key(j.get("company")), key(j.get("title")), key(j.get("location"))) for j in known.values()}
    new, changed = [], []
    for j in dedupe(raw):
        k = (key(j["company"]), key(j["title"]), key(j["location"]))
        if j["id"] in known:
            if known[j["id"]].get("hash") != j["hash"]:
                changed.append(j)
        elif k not in known_keys:
            new.append(j)
    if not a.dry_run and (new or changed):
        rows = known
        for j in new:
            rows[j["id"]] = j
        for j in changed:
            rows[j["id"]] = {**rows[j["id"]], **{f: j[f] for f in FIELDS + ["hash"]}, "changed_on": today().isoformat()}
        write_jsonl(jobs_path(), list(rows.values()))
        inbox_add(new + changed)
    emit({"ok": True, "checked": len(raw), "new": [compact(j) for j in new],
          "changed": [compact(j) for j in changed], "recorded": not a.dry_run,
          "coverage": data.get("coverage") if isinstance(data, dict) else None})


def cmd_show(a):
    pool = {j["id"]: j for j in read_jsonl(home() / "inbox.jsonl")}
    pool.update({j["id"]: {**pool.get(j["id"], {}), **j} for j in read_jsonl(jobs_path())})
    found = [pool[i] for i in a.ids if i in pool]
    emit({"ok": True, "jobs": found, "missing": [i for i in a.ids if i not in pool]})


def clean_gap(g):
    return re.sub(r"\s+", " ", str(g).strip().lower())


def cmd_save(a):
    incoming = read_list(a.file)
    inbox = {j["id"]: j for j in read_jsonl(home() / "inbox.jsonl")}
    rows = {j["id"]: j for j in read_jsonl(jobs_path())}
    errors, saved = [], 0
    for x in incoming:
        jid = x.get("id")
        if x.get("tier") not in TIERS:
            errors.append(f"{jid}: tier must be one of {TIERS}")
            continue
        if x.get("likelihood") not in BANDS:
            errors.append(f"{jid}: likelihood must be one of {BANDS}")
            continue
        base = rows.get(jid) or inbox.get(jid)
        if base is None and not x.get("title"):
            errors.append(f"{jid}: unknown id and no job fields given (run normalize first)")
            continue
        merged = norm_job({**(base or {}), **x, "first_seen": (base or x).get("first_seen")})
        merged["gaps"] = [clean_gap(g) for g in x.get("gaps") or [] if str(g).strip()]
        merged["score"] = int(x["score"]) if x.get("score") is not None else None
        merged["ranked_on"] = today().isoformat()
        rows[merged["id"]] = merged
        saved += 1
    write_jsonl(jobs_path(), list(rows.values()))
    emit({"ok": not errors, "saved": saved, "errors": errors, "total_jobs": len(rows)}, 0 if not errors else 1)


# ---------------------------------------------------------------- gaps / pay

def gap_report(rows):
    scored = [j for j in rows if j.get("tier") in TIERS]
    near = [j for j in scored if j["tier"] == "Stretch" or (j["tier"] == "Skip" and not j.get("filter_reason"))]
    near_ids = {j["id"] for j in near}
    table = {}
    for j in scored:
        gaps = [clean_gap(g) for g in j.get("gaps") or []]
        for i, g in enumerate(dict.fromkeys(gaps)):
            t = table.setdefault(g, {"gap": g, "total": 0, "by_tier": {k: 0 for k in TIERS},
                                     "near_miss": 0, "unlock": 0, "only_gap": 0, "as_must_have": 0})
            t["total"] += 1
            t["by_tier"][j["tier"]] += 1
            if g in [clean_gap(m) for m in j.get("must_have") or []]:
                t["as_must_have"] += 1
            if j["id"] in near_ids:
                t["near_miss"] += 1
                if i == 0:
                    t["unlock"] += 1
                if len(gaps) == 1:
                    t["only_gap"] += 1
    ordered = sorted(table.values(), key=lambda t: (-t["unlock"], -t["near_miss"], -t["total"], t["gap"]))
    return {"ok": True, "jobs_scored": len(scored), "near_miss_jobs": len(near), "enough_data": len(scored) >= 10,
            "by_tier": {k: sum(1 for j in scored if j["tier"] == k) for k in TIERS}, "gaps": ordered}


def cmd_gaps(a):
    emit(gap_report(read_jsonl(a.jobs or jobs_path())))


def cmd_pay(a):
    kws = [k.lower() for k in a.keywords]
    by_cur = {}
    for j in read_jsonl(jobs_path()):
        if all(k in (j.get("title") or "").lower() for k in kws) and (j.get("salary_min") or j.get("salary_max")):
            by_cur.setdefault(j.get("currency") or "unknown", []).append(j)
    res = {}
    for cur, js in by_cur.items():
        lows = [j["salary_min"] for j in js if j.get("salary_min")]
        highs = [j["salary_max"] for j in js if j.get("salary_max")]
        res[cur] = {"postings": len(js), "median_min": statistics.median(lows) if lows else None,
                    "median_max": statistics.median(highs) if highs else None}
    emit({"ok": True, "keywords": kws, "by_currency": res,
          "note": "Only postings that state a salary are counted."})


# ---------------------------------------------------------------- tracker

def tracker_path():
    return home() / "tracker.csv"


def read_tracker(path=None):
    p = Path(path or tracker_path())
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_tracker(rows):
    tmp = tracker_path().with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=TRACKER_COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(tracker_path())


def history(row):
    out = []
    for part in (row.get("history") or "").split(";"):
        if ":" in part:
            d, s = part.split(":", 1)
            out.append((d.strip(), s.strip()))
    return out


def parse_date(s):
    try:
        return date.fromisoformat((s or "").strip()[:10])
    except ValueError:
        return None


def cmd_track(a):
    rows = read_tracker()
    t = today()
    if a.action == "list":
        for r in rows:
            fu = parse_date(r.get("follow_up"))
            r["overdue"] = bool(fu and fu <= t and r.get("stage") in ACTIVE)
        emit({"ok": True, "count": len(rows), "rows": rows, "overdue": [r for r in rows if r["overdue"]]})
    guard_write(f"track {a.action}")
    d = (a.date or a.applied or t.isoformat())
    if not parse_date(d):
        fail(f"Bad date '{d}'. Use YYYY-MM-DD.")
    if a.action == "add":
        if any(r["job_id"] == a.job_id for r in rows):
            fail(f"{a.job_id} is already in the tracker. Use `track update`.")
        job = next((j for j in read_jsonl(jobs_path()) if j["id"] == a.job_id), {})
        src = a.source or {"ats": "direct", "api": "board", "web": "board"}.get(job.get("source"), "")
        row = {"job_id": a.job_id, "company": a.company or job.get("company", ""),
               "role": a.role or job.get("title", ""), "source": src,
               "tier_at_apply": job.get("tier", ""), "likelihood_at_apply": job.get("likelihood", ""),
               "applied": d, "stage": "applied", "last_update": d,
               "follow_up": a.follow_up or (parse_date(d) + timedelta(days=7)).isoformat(),
               "history": f"{d}:applied", "notes": a.note or ""}
        rows.append(row)
    else:
        row = next((r for r in rows if r["job_id"] == a.job_id), None) or fail(f"{a.job_id} is not in the tracker.")
        if a.stage not in STAGES:
            fail(f"Stage must be one of {STAGES}.")
        row["stage"] = a.stage
        row["last_update"] = d
        row["history"] = ";".join(filter(None, [row.get("history"), f"{d}:{a.stage}"]))
        if a.stage not in ACTIVE:
            row["follow_up"] = ""
        if a.follow_up:
            row["follow_up"] = a.follow_up
        if a.note:
            row["notes"] = "; ".join(filter(None, [row.get("notes"), a.note]))
    write_tracker(rows)
    emit({"ok": True, "row": row, "count": len(rows)})


def rate(group, min_n):
    n = len(group)
    replied = sum(1 for r in group if r["_replied"])
    interviews = sum(1 for r in group if r["_reached"] & {"interview", "offer"})
    return {"n": n, "replied": replied, "interviews": interviews,
            "reply_rate": round(replied / n, 2) if n else None, "too_early": n < min_n}


def compute_stats(rows, min_n=5):
    t = today()
    iso = t.isocalendar()
    week = f"{iso[0]}-W{iso[1]:02d}"
    for r in rows:
        h = history(r)
        r["_reached"] = {s for _, s in h} | {r.get("stage", "")}
        r["_replied"] = bool(r["_reached"] & REPLIED)
        applied = parse_date(r.get("applied"))
        first = next((parse_date(d) for d, s in h if s in REPLIED), None)
        r["_days_to_reply"] = (first - applied).days if first and applied else None
    def group_by(field):
        groups = {}
        for r in rows:
            groups.setdefault(r.get(field) or "unknown", []).append(r)
        return {k: rate(v, min_n) for k, v in sorted(groups.items())}
    this_week = [r for r in rows if (parse_date(r.get("applied")) or date.min).isocalendar()[:2] == iso[:2]]
    days = [r["_days_to_reply"] for r in rows if r["_days_to_reply"] is not None]
    active = [r for r in rows if r.get("stage") in ACTIVE]
    overdue = [r for r in active if (fu := parse_date(r.get("follow_up"))) and fu <= t]
    stale = [r for r in active if (parse_date(r.get("last_update")) or parse_date(r.get("applied")) or t)
             <= t - timedelta(days=14)]
    pick = lambda rs: [{k: r.get(k) for k in ("job_id", "company", "role", "stage", "follow_up", "last_update")}
                       for r in rs]
    return {
        "ok": True, "today": t.isoformat(), "week": week, "min_sample": min_n,
        "total": rate(rows, min_n),
        "this_week": {"applications": len(this_week),
                      "by_tier": {k: sum(1 for r in this_week if r.get("tier_at_apply") == k) for k in TIERS}},
        "by_stage": {s: sum(1 for r in rows if r.get("stage") == s) for s in STAGES},
        "funnel": {s: sum(1 for r in rows if s in r["_reached"]) for s in ("applied", "screen", "interview", "offer")},
        "by_source": group_by("source"),
        "by_tier": group_by("tier_at_apply"),
        "by_likelihood": group_by("likelihood_at_apply"),
        "days_to_reply": {"n": len(days), "median": statistics.median(days) if days else None},
        "overdue_followups": {"n": len(overdue), "rows": pick(overdue)},
        "stale_14_days": {"n": len(stale), "rows": pick(stale)},
    }


def cmd_stats(a):
    emit(compute_stats(read_tracker(a.tracker), a.min_sample))


# ---------------------------------------------------------------- profile / status

def split(v):
    return [x.strip() for x in re.split(r"[;\n]", v or "") if x.strip()]


def profile(path=None):
    p = Path(path or home() / "profile.md")
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*[-*]\s*\**([^:*]+?)\**\s*:\s*(.*)$", line)
        if m:
            out[m.group(1).strip().lower()] = m.group(2).strip()
    return out


REQUIRED = ["target roles", "location", "remote preference", "work rights"]


def cmd_status(a):
    h = home()
    p = profile()
    missing = [k for k in REQUIRED if not p.get(k)] if p else REQUIRED
    jobs = read_jsonl(jobs_path())
    files = {n: (h / n).exists() for n in ("profile.md", "resume-original.pdf", "resume-master.md",
                                           "watchlist.json", "jobs.jsonl", "tracker.csv")}
    ready = files["profile.md"] and files["resume-master.md"] and not missing
    emit({"ok": True, "home": str(h), "ready": ready, "files": files, "profile": p,
          "missing_profile_fields": missing, "jobs_seen": len(jobs),
          "jobs_ranked": sum(1 for j in jobs if j.get("tier") in TIERS),
          "tracked": len(read_tracker()), "watchlist": len(watchlist()),
          "readonly": os.environ.get("SHERPA_READONLY") == "1",
          "next": None if ready else "Run /sherpa:setup first."})


# ---------------------------------------------------------------- schedule

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
JOBS = {
    "morning": {"label": "Sherpa morning brief", "outdir": "briefs", "days": "brief days",
                "time": "brief time", "default_days": "Mon;Tue;Wed;Thu;Fri", "default_time": "08:00"},
    "weekly": {"label": "Sherpa weekly review", "outdir": "weekly", "days": "weekly day",
               "time": "weekly time", "default_days": "Fri", "default_time": "16:30"},
}


def cmd_schedule(a):
    guard_write("schedule")
    spec, p, h = JOBS[a.which], profile(), home()
    days = [d[:3].title() for d in split(p.get(spec["days"]) or spec["default_days"])]
    if not days or any(d not in DAYS for d in days):
        fail(f"Bad days {days}. Use Mon;Tue;... in profile.md.")
    hhmm = p.get(spec["time"]) or spec["default_time"]
    if not re.fullmatch(r"\d{1,2}:\d{2}", hhmm):
        fail(f"Bad time '{hhmm}'. Use HH:MM (24-hour) in profile.md.")
    hour, minute = map(int, hhmm.split(":"))
    claude = shutil.which("claude") or "claude"
    sched = h / "schedule"
    sched.mkdir(exist_ok=True)
    (h / spec["outdir"]).mkdir(exist_ok=True)
    # dontAsk mode denies anything not allowed here. File writes are matched by Edit(path) rules, and a
    # blanket "Edit" deny would override this allow, so the only write permission is the output folder.
    tools = ["Read", "Glob", "Grep", "WebSearch", "WebFetch", "Bash(python *)", "Bash(python3 *)", "Bash(py *)",
             f"Edit(./{spec['outdir']}/**)"]
    deny = ["NotebookEdit", "mcp__claude-in-chrome", "Agent", "PowerShell"]
    plugin_flag = f' --plugin-dir "{Path(a.plugin_dir).resolve()}"' if a.plugin_dir else ""
    prompt = f"/sherpa:{a.which} scheduled"
    log = sched / f"{a.which}.log"
    windows = platform.system() == "Windows"
    q = lambda xs: " ".join(f'"{x}"' for x in xs)
    claude_cmd = (f'"{claude}" -p "{prompt}" --permission-mode dontAsk{plugin_flag} '
                  f"--allowedTools {q(tools)} --disallowedTools {q(deny)}")
    if windows:
        script = sched / f"{a.which}.cmd"
        script.write_text(f'@echo off\r\ncd /d "{h}"\r\nset SHERPA_READONLY=1\r\nset SHERPA_HOME={h}\r\n'
                          f'{claude_cmd} >> "{log}" 2>&1\r\n', encoding="utf-8")
        task = spec["label"]
        register = ["schtasks", "/Create", "/F", "/TN", task, "/TR", f'"{script}"', "/SC", "WEEKLY",
                    "/D", ",".join(d.upper() for d in days), "/ST", f"{hour:02d}:{minute:02d}"]
        remove = ["schtasks", "/Delete", "/F", "/TN", task]
    else:
        script = sched / f"{a.which}.sh"
        script.write_text(f'#!/bin/sh\ncd "{h}" || exit 1\nexport SHERPA_READONLY=1 SHERPA_HOME="{h}"\n'
                          f'{claude_cmd} >> "{log}" 2>&1\n', encoding="utf-8")
        script.chmod(0o755)
        cron_days = ",".join(str((DAYS.index(d) + 1) % 7) for d in days)
        line = f'{minute} {hour} * * {cron_days} /bin/sh "{script}" # sherpa:{a.which}'
        register = ["sh", "-c", f'(crontab -l 2>/dev/null | grep -v "# sherpa:{a.which}"; echo \'{line}\') | crontab -']
        remove = ["sh", "-c", f'crontab -l 2>/dev/null | grep -v "# sherpa:{a.which}" | crontab -']
    result = {"ok": True, "job": a.which, "days": days, "time": f"{hour:02d}:{minute:02d}",
              "timezone_note": "Runs in this computer's local time. The computer must be on and logged in.",
              "script": str(script), "log": str(log), "register_command": register, "remove_command": remove,
              "allowed_tools": tools, "denied_tools": deny, "installed": False, "removed": False}
    if a.install or a.remove:
        r = subprocess.run(remove if a.remove else register, capture_output=True, text=True)
        result.update({"installed": a.install and r.returncode == 0, "removed": a.remove and r.returncode == 0,
                       "ok": r.returncode == 0, "output": (r.stdout + r.stderr).strip()})
    emit(result, 0 if result["ok"] else 1)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p = sub.add_parser("probe"); p.add_argument("target", nargs="?"); p.add_argument("--match")
    p.add_argument("--watchlist", action="store_true"); p.add_argument("--limit", type=int, default=30)
    p.add_argument("--max", type=int, default=60); p.add_argument("--company")
    w = sub.add_parser("watch"); w.add_argument("action", choices=["add", "list"]); w.add_argument("name", nargs="?")
    w.add_argument("--url")
    x = sub.add_parser("api"); x.add_argument("name"); x.add_argument("--query", required=True)
    x.add_argument("--where"); x.add_argument("--country")
    for n in ("normalize", "dedupe", "save"):
        sub.add_parser(n).add_argument("file", nargs="?")
    s = sub.add_parser("seen"); s.add_argument("file", nargs="?"); s.add_argument("--dry-run", action="store_true")
    sub.add_parser("show").add_argument("ids", nargs="+")
    sub.add_parser("gaps").add_argument("--jobs")
    sub.add_parser("pay").add_argument("keywords", nargs="+")
    st = sub.add_parser("stats"); st.add_argument("tracker", nargs="?"); st.add_argument("--min-sample", type=int, default=5)
    t = sub.add_parser("track"); t.add_argument("action", choices=["add", "update", "list"])
    t.add_argument("job_id", nargs="?"); t.add_argument("--job-id", dest="job_id_opt")
    for f in ("stage", "date", "applied", "follow-up", "note", "company", "role", "source"):
        t.add_argument(f"--{f}")
    sc = sub.add_parser("schedule"); sc.add_argument("which", choices=list(JOBS))
    sc.add_argument("--install", action="store_true"); sc.add_argument("--remove", action="store_true")
    sc.add_argument("--plugin-dir")
    a = ap.parse_args()
    if a.cmd == "track":
        a.job_id = a.job_id or a.job_id_opt
        if a.action != "list" and not a.job_id:
            fail("track add/update needs a job id.")
    {"status": cmd_status, "probe": cmd_probe, "watch": cmd_watch, "api": cmd_api, "normalize": cmd_normalize,
     "dedupe": cmd_dedupe, "seen": cmd_seen, "show": cmd_show, "save": cmd_save, "gaps": cmd_gaps,
     "pay": cmd_pay, "stats": cmd_stats, "track": cmd_track, "schedule": cmd_schedule}[a.cmd](a)


if __name__ == "__main__":
    main()
