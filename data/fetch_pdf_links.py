"""
fetch_pdf_links.py
==================
Fetches direct PDF links for all papers in paper_links.csv using 3 methods:
  1. arXiv API           — best for AI/ML papers; free, no key needed
  2. Crossref + Unpaywall — DOI lookup + open-access PDF index
  3. OpenAlex            — final fallback for remaining OA papers

Features:
  - Exponential backoff on 429 / rate-limit / timeout errors
  - Auto-saves progress to checkpoint.json — safe to interrupt and re-run
  - Outputs direct_pdf_links.csv and download_papers.py

HOW TO RUN (Windows):
  1. pip install requests
  2. Place this file and paper_links.csv in the same folder
  3. python fetch_pdf_links.py
  4. python download_papers.py   <- downloads all PDFs into a "papers" folder
"""

import csv
import time
import re
import json
import os
import requests
from xml.etree import ElementTree

# ── Config ───────────────────────────────────────────────────────────────────
INPUT_CSV       = "paper_links.csv"
OUTPUT_CSV      = "direct_pdf_links.csv"
DOWNLOAD_SCRIPT = "download_papers.py"
CHECKPOINT_FILE = "checkpoint.json"         # auto-saves progress after each paper

UNPAYWALL_EMAIL = "admissions@smu.edu.sg"  # replace with any valid email (not verified)

ARXIV_DELAY     = 3.0  # seconds between arXiv calls — generous to avoid 429
API_DELAY       = 1.0  # seconds between Crossref / Unpaywall / OpenAlex calls
MAX_RETRIES     = 5    # retry attempts on rate-limit errors
# ─────────────────────────────────────────────────────────────────────────────


def backoff_request(method: str, url: str, max_retries=MAX_RETRIES, **kwargs):
    """
    GET/HEAD wrapper with exponential backoff.
    Retries on: 429 Too Many Requests, 503 Service Unavailable,
                connection errors, and timeouts.
    """
    for attempt in range(max_retries):
        try:
            resp = getattr(requests, method)(url, timeout=20, **kwargs)
            if resp.status_code in (429, 503):
                wait = (2 ** attempt) * 5   # 5s → 10s → 20s → 40s → 80s
                print(f"    [Rate limited {resp.status_code}] Waiting {wait}s "
                      f"(retry {attempt + 1}/{max_retries})...")
                time.sleep(wait)
                continue
            return resp
        except requests.exceptions.ConnectionError as e:
            wait = (2 ** attempt) * 3
            print(f"    [Connection error] {e}. Retrying in {wait}s...")
            time.sleep(wait)
        except requests.exceptions.Timeout:
            wait = (2 ** attempt) * 3
            print(f"    [Timeout] Retrying in {wait}s...")
            time.sleep(wait)
    print(f"    [Failed] All {max_retries} retries exhausted for {url}")
    return None


# ── Method 1: arXiv ──────────────────────────────────────────────────────────

def get_arxiv_pdf(title: str):
    """Exact title search on arXiv. Returns (pdf_url, arxiv_id) or (None, None)."""
    resp = backoff_request(
        "get", "http://export.arxiv.org/api/query",
        params={"search_query": f'ti:"{title}"', "max_results": 1}
    )
    if resp is None or resp.status_code != 200:
        return None, None
    try:
        root  = ElementTree.fromstring(resp.text)
        ns    = "{http://www.w3.org/2005/Atom}"
        entry = root.find(f"{ns}entry")
        if entry is None:
            return None, None
        title_text = (entry.find(f"{ns}title").text or "").lower()
        if "no matches" in title_text:
            return None, None
        arxiv_id = entry.find(f"{ns}id").text.strip().split("/abs/")[-1]
        return f"https://arxiv.org/pdf/{arxiv_id}", arxiv_id
    except Exception as e:
        print(f"    [arXiv parse error] {e}")
    return None, None


# ── Method 2: Crossref → Unpaywall ───────────────────────────────────────────

def get_doi(title: str):
    """Resolve a paper title to a DOI via Crossref REST API."""
    resp = backoff_request(
        "get", "https://api.crossref.org/works",
        params={"query.bibliographic": title, "rows": 1},
        headers={"User-Agent": "PaperFetcher/1.0 (mailto:your@email.com)"}
    )
    if resp is None or resp.status_code != 200:
        return None
    try:
        items = resp.json().get("message", {}).get("items", [])
        return items[0].get("DOI") if items else None
    except Exception as e:
        print(f"    [Crossref parse error] {e}")
    return None


def get_unpaywall_pdf(doi: str):
    """Retrieve open-access PDF URL from Unpaywall by DOI."""
    resp = backoff_request(
        "get", f"https://api.unpaywall.org/v2/{doi}",
        params={"email": UNPAYWALL_EMAIL}
    )
    if resp is None or resp.status_code != 200:
        return None
    try:
        oa = resp.json().get("best_oa_location") or {}
        return oa.get("url_for_pdf")
    except Exception as e:
        print(f"    [Unpaywall parse error] {e}")
    return None


# ── Method 3: OpenAlex ───────────────────────────────────────────────────────

def get_openalex_pdf(doi: str = None, title: str = None):
    """
    Retrieve open-access PDF from OpenAlex.
    Prefers DOI lookup; falls back to title search if no DOI available.
    """
    if doi:
        resp = backoff_request("get", f"https://api.openalex.org/works/doi:{doi}")
    elif title:
        resp = backoff_request(
            "get", "https://api.openalex.org/works",
            params={"search": title, "per_page": 1}
        )
    else:
        return None

    if resp is None or resp.status_code != 200:
        return None
    try:
        data = resp.json()
        if "results" in data:                          # title search response
            data = data["results"][0] if data["results"] else {}
        oa = data.get("best_oa_location") or {}
        return oa.get("pdf_url")
    except Exception as e:
        print(f"    [OpenAlex parse error] {e}")
    return None


# ── Checkpoint helpers ───────────────────────────────────────────────────────

def load_checkpoint() -> dict:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_checkpoint(data: dict):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ── Windows-safe filename ────────────────────────────────────────────────────

def sanitize_filename(title: str) -> str:
    s = re.sub(r'[<>:"/\\|?*]', '', title).strip()
    s = re.sub(r'\s+', '_', s)
    return s[:100] + ".pdf"


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    with open(INPUT_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total      = len(rows)
    checkpoint = load_checkpoint()
    results    = []

    print(f"Processing {total} papers using 3-method search...\n")
    if checkpoint:
        print(f"  Resuming — {len(checkpoint)} papers already in checkpoint.\n")

    for i, row in enumerate(rows, 1):
        title = row["title"].strip()
        key   = str(row.get("index", i))

        if key in checkpoint:
            results.append(checkpoint[key])
            print(f"[{i:>3}/{total}] (cached) {title[:65]}")
            continue

        print(f"\n[{i:>3}/{total}] {title[:70]}")

        doi    = None
        pdf    = None
        source = ""

        # ── Method 1: arXiv ──────────────────────────────────
        pdf, arxiv_id = get_arxiv_pdf(title)
        time.sleep(ARXIV_DELAY)
        if pdf:
            source = f"arXiv:{arxiv_id}"
            print(f"         [1] arXiv     -> {pdf}")

        # ── Method 2: Crossref + Unpaywall ───────────────────
        if not pdf:
            doi = get_doi(title)
            time.sleep(API_DELAY)
            if doi:
                print(f"         [2] DOI       -> {doi}")
                pdf = get_unpaywall_pdf(doi)
                time.sleep(API_DELAY)
                if pdf:
                    source = "Unpaywall"
                    print(f"         [2] Unpaywall -> {pdf}")

        # ── Method 3: OpenAlex ───────────────────────────────
        if not pdf:
            pdf = get_openalex_pdf(doi=doi, title=(title if not doi else None))
            time.sleep(API_DELAY)
            if pdf:
                source = "OpenAlex"
                print(f"         [3] OpenAlex  -> {pdf}")

        if not pdf:
            print(f"         [x] Not found by any method")

        record = {
            "index"  : key,
            "title"  : title,
            "doi"    : doi or "",
            "pdf_url": pdf or "",
            "source" : source,
        }
        results.append(record)
        checkpoint[key] = record
        save_checkpoint(checkpoint)   # persist after every paper

    # ── Write results CSV ────────────────────────────────────────────────────
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["index", "title", "doi", "pdf_url", "source"])
        writer.writeheader()
        writer.writerows(results)

    found   = [r for r in results if r["pdf_url"]]
    missing = [r for r in results if not r["pdf_url"]]

    # ── Write Python downloader (no wget required on Windows) ────────────────
    with open(DOWNLOAD_SCRIPT, "w", encoding="utf-8") as f:
        f.write('"""\ndownload_papers.py\nDownloads all found PDFs into a "papers" subfolder.\nRun: python download_papers.py\n"""\n\n')
        f.write("import requests, os\n\n")
        f.write('os.makedirs("papers", exist_ok=True)\n\n')
        f.write("papers = [\n")
        for r in found:
            fname = sanitize_filename(r["title"]).replace("\\", "\\\\")
            f.write(f'    ("{r["pdf_url"]}", "papers/{fname}"),\n')
        f.write("]\n\n")
        f.write("total = len(papers)\n")
        f.write("for i, (url, path) in enumerate(papers, 1):\n")
        f.write('    print(f"[{i}/{total}] Downloading {os.path.basename(path)}...")\n')
        f.write("    try:\n")
        f.write("        r = requests.get(url, timeout=60, stream=True)\n")
        f.write("        r.raise_for_status()\n")
        f.write('        with open(path, "wb") as f:\n')
        f.write("            for chunk in r.iter_content(chunk_size=8192):\n")
        f.write("                f.write(chunk)\n")
        f.write('        print("  Saved.")\n')
        f.write("    except Exception as e:\n")
        f.write('        print(f"  Failed: {e}")\n')
        f.write('\nprint("\\nAll done!")\n')

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Found  : {len(found)}/{total}")
    print(f"  Missing: {len(missing)}/{total}")
    print(f"\n  {OUTPUT_CSV}   <- PDF links")
    print(f"  {DOWNLOAD_SCRIPT} <- run to download all PDFs")
    print(f"  {CHECKPOINT_FILE}     <- delete this to start fresh")
    print(f"{'='*60}")

    if missing:
        print("\nNot found by any method:")
        for r in missing:
            print(f"  [{r['index']:>3}] {r['title']}")


if __name__ == "__main__":
    main()