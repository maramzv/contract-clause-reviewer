# Contract Clause Extraction and Review

A web app that turns a batch of commercial contracts into a first-pass clause review table. Every finding shows the exact contract wording and its page. Every category the tool could not find is flagged for human review instead of being left blank.

**Owners:** Kerrian Gordon and Mara Munoz

The source of truth is the [final PRD](docs/02-prd/FINAL%20-%20Contract%20Clause%20Extraction%20and%20Review%20-%20%20PRD%20-%20Kerrian%20Gordon%20%26%20Mara%20Munoz.md). This README summarizes it and the code in `src/`. If they disagree, the PRD wins.

## The problem

Junior associates and contracts paralegals reviewing a batch of contracts for diligence repeat the same work: find the same clause types in every agreement, copy quotations and page references into a spreadsheet, and wonder whether an empty keyword search means the clause is truly absent. Senior lawyers then ask "where does the contract actually say that?" before trusting the table.

These pain points are **hypotheses**, not established facts. No posting says that finding clauses is the slow step, and the time saved has not been measured. The persona (Maya, a junior associate reviewing 30 contracts before an acquisition) is illustrative.

## What it does

1. Upload contracts (PDF or text) and choose the clause categories to check.
2. The system finds candidate passages and keeps only quotations that appear **word for word** in the contract.
3. Maya sees each finding with its quotation, page and status, then **accepts** it, **removes** it, or **restores** a removed one.
4. Download the reviewed table as CSV with the columns document, category, quote, page, review and question (the question column stays empty until flagging is built). Removed findings are left out, and each category with no verified finding appears as a bracketed row such as `[Not found, review required]` or `[Failed to process]`.

Each run in the app creates a new review named by the time of the run.

**Checklist categories (mapped to CUAD labels):**

| Category | CUAD label |
|---|---|
| Assignment | Anti-Assignment |
| Change of control | Change Of Control |
| Termination for convenience | Termination For Convenience |
| Renewal | Renewal Term |
| Governing law | Governing Law |

**Each category in each contract ends in one of three visible states:** Found · Not found, review required · Failed to process. If every finding in a category is removed, it goes back to "Not found, review required", so removing a false match never reads as a confirmed absence.

## Two guarantees

- **100% verbatim quotations.** A quotation is shown only if it is found word for word in the contract after whitespace normalization (minimum 15 characters). Anything else is dropped.
- **100% visible gaps.** Any contract and category pair without a verified finding is labeled "not found, review required" or "failed to process". A missing result is never treated as a confirmed absence.

## Scope

**P0 (committed for the build window):** multi-file upload, failed-file reporting with reason, category selection, quotation + page for each finding, per-category status, accept/remove, CSV export.

**P1/P2:** highlighting in full text, marking a category as reviewed, flagging a question for a senior lawyer, adding a missed passage, filters, custom categories. Built only if P0 is finished and demonstrated.

**Non-goals:** legal interpretation or risk scoring, OCR for scanned PDFs, non-English contracts, drafting/redlining, multi-user accounts, processing real client contracts with a hosted model, scoring notice of non-renewal.

## How it's built

| Layer | Choice |
|---|---|
| Frontend | Streamlit (one Python process) |
| Backend | `clause_review` Python package in `src/`: ingest → chunk → extract → verify → store → export |
| Database | SQLite (one local file) |
| Model | Claude Sonnet via the facilitator's API key (environment variable, never stored). A mock provider runs offline and is the default. |

**Pipeline:**

1. **Ingest:** pypdf reads each page and records page starts. Unreadable or scanned files become "Failed to process".
2. **Chunk:** about 3,000-character windows with 300 characters of overlap, cut at paragraph or sentence boundaries.
3. **Extract:** a regex pass finds candidate sentences, then one model call per chunk returns category and exact quotation as JSON. Responses are cached by a hash of provider, model and prompt.
4. **Verify:** drop any quotation not found verbatim. Where findings in a category overlap, the model's quotation is kept over a regex one, and among quotations from the same source the tightest is kept.
5. **Store:** findings and category statuses go to SQLite.
6. **Review and export:** accept, remove or restore, then download the CSV.

Locations are PDF page numbers. A text file counts as one page. Section headings are not detected.

**Data model:** Project, Document, Finding, CategoryStatus, LLMCache (see PRD section 4d).

## Run it

From the `src/` folder:

```
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install streamlit pypdf pytest anthropic    # anthropic is only needed for the hosted model
python -m pytest -q             # runs offline with the mock provider
streamlit run app.py            # the review screen, on the mock provider by default
```

Try it with `src/samples/sample_contract.txt`. The mock provider finds clauses with keyword rules, so its results say nothing about real model quality, and the screen says so.

**Settings** (copy `.env.example` to `.env`; it is git-ignored, so never commit a real key):

| Variable | What it does |
|---|---|
| `CLAUSE_PROVIDER` | `mock` (default), `anthropic` or `local` |
| `ANTHROPIC_API_KEY` | Needed only for `anthropic` |
| `CLAUSE_MODEL` | Model name; the code defaults to `claude-sonnet-5-5` |
| `CLAUSE_WORKERS` | Parallel model calls (1 = one at a time) |
| `CLAUSE_BUDGET_USD`, `CLAUSE_PRICE_IN`, `CLAUSE_PRICE_OUT` | Spend limit. All three are needed together, and prices come from the price list. None are built in. |
| `CLAUSE_DB` | SQLite file for the review screen (default `review.db`) |

More detail, and the assumptions that are tested vs. still unmeasured, are in [src/README.md](src/README.md).

## Data and privacy

Evaluation and demos use **public contracts from CUAD** (510 contracts, 41 categories, CC BY 4.0). Real deal contracts should not be sent to a hosted model. The database stores the full text of every uploaded contract, so use public contracts only. Development uses 408 CUAD contracts. The 102-contract test split stays untouched until the answer key is frozen.

## Evaluation (after the build window)

| Goal | Target |
|---|---|
| Recall per category on the 102 test contracts (50% span overlap) | Average ≥ 0.80 |
| Precision after verification, compared against a regex-only baseline | Average ≥ 0.70, and F1 at least 10 points above baseline |
| Time saved, in a counterbalanced pilot with ≥ 2 reviewers | Median per-contract time at least 30% lower, with no more missed clauses |
| Processing time for the 30 largest test contracts (empty cache) | ≤ 30 minutes |

The answer key, written category definitions and extractor prompts are frozen and tagged at the end of Nov 7. The first test-split run is on or after Nov 9.

## Status

**Built:** upload, category choice, findings with quotation, page and category status, failed files listed with the reason, accept/remove/restore, CSV download, the model providers with a spend limit and response cache, and 25 passing tests (offline, on the mock provider).

**Not built yet:** marking a category as reviewed (P1), the CUAD loader, and the evaluation script. No real-model run has been made, so cost and latency are unmeasured.

## Repo layout

```
docs/00-assignment/   the assignment breakdown
docs/01-research/     job descriptions and early design notes
docs/02-prd/          the final PRD (source of truth)
intro/                the intro slideshow (open intro/index.html)
src/                  the app, the clause_review package and tests
```
