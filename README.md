# Contract Clause Extraction and Review

A web app that turns a batch of commercial contracts into a first-pass clause review table. Every finding shows the exact contract wording and its page. Every category the tool could not find is flagged for human review instead of being left blank.

**Owners:** Kerrian Gordon and Mara Munoz

## The problem

Junior associates and contracts paralegals reviewing a batch of contracts for diligence repeat the same work: find the same clause types in every agreement, copy quotations and page references into a spreadsheet, and wonder whether an empty keyword search means the clause is truly absent. Senior lawyers then ask "where does the contract actually say that?" before trusting the table.

These pain points are **hypotheses**, not established facts. The persona (Maya, a junior associate reviewing 30 contracts before an acquisition) is illustrative. 

## What it does

1. Create a review and upload contracts (PDF or text).
2. Choose the clause categories to check.
3. The system finds candidate passages and keeps only quotations that appear **word for word** in the contract.
4. Maya sees each finding with its quotation, page and status, then accepts it or removes it.
5. Export the reviewed table to CSV: contract, category, quotation, location, review state, note.

**Checklist categories (mapped to CUAD labels):**

| Category | CUAD label |
|---|---|
| Assignment | Anti-Assignment |
| Change of control | Change Of Control |
| Termination for convenience | Termination For Convenience |
| Renewal | Renewal Term |
| Governing law | Governing Law |

**Each category in each contract ends in one of three visible states:** Found · Not found, review required · Failed to process.

## Two guarantees

- **100% verbatim quotations.** A quotation is shown only if it is found word for word in the contract after whitespace normalization (minimum 15 characters). Anything else is dropped.
- **100% visible gaps.** Any contract and category pair without a verified finding is labeled "not found, review required" or "failed to process". A missing result is never treated as a confirmed absence.

## Scope

**P0 (committed for the build window):** multi-file upload, failed-file reporting with reason, category selection, quotation + page for each finding, per-category status, accept/remove, CSV export.

**P1/P2:** highlighting in full text, flagging a question for a senior lawyer, adding a missed passage, filters, custom categories. Built only if P0 is finished and demonstrated.

**Non-goals:** legal interpretation or risk scoring, OCR for scanned PDFs, non-English contracts, drafting/redlining, multi-user accounts, processing real client contracts with a hosted model, scoring notice of non-renewal.

## How it's built

| Layer | Choice |
|---|---|
| Frontend | Streamlit (one Python process) |
| Backend | `clause_review` Python package: ingest → chunk → extract → verify → store → export |
| Database | SQLite (one local file) |
| Model | Claude Sonnet via the facilitator's API key (environment variable, never stored). A mock provider runs offline and is the last-resort demo fallback. |


**Pipeline:**

1. **Ingest:** pypdf reads each page and records page starts. Unreadable or scanned files become "Failed to process".
2. **Chunk:** about 3,000-character windows with 300 characters of overlap, cut at paragraph or sentence boundaries.
3. **Extract:** a regex pass finds candidates, then one model call per chunk returns category and exact quotation as JSON. Responses are cached by a hash of provider, model and prompt.
4. **Verify:** drop any quotation not found verbatim. Merge overlapping findings in a category, keeping the shortest.
5. **Store:** findings and category statuses go to SQLite.
6. **Review and export:** accept or remove, then export to CSV.

Locations are PDF page numbers. A text file counts as one page. Section headings are not detected.

**Data model:** Project, Document, Finding, CategoryStatus, LLMCache (see PRD section 4d).


## Data and privacy

Evaluation and demos use **public contracts from CUAD** (510 contracts, 41 categories, CC BY 4.0). Real deal contracts should not be sent to a hosted model. Development uses 408 CUAD contracts. The 102-contract test split stays untouched until the answer key is frozen.

## Evaluation (after the build window)

| Goal | Target |
|---|---|
| Recall per category on the 102 test contracts (50% span overlap) | Average ≥ 0.80 |
| Precision after verification, compared against a regex-only baseline | Average ≥ 0.70, and F1 at least 10 points above baseline |
| Time saved, in a counterbalanced pilot with ≥ 2 reviewers | Median per-contract time at least 30% lower, with no more missed clauses |
| Processing time for the 30 largest test contracts (empty cache) | ≤ 30 minutes |

The answer key, written category definitions and extractor prompts are frozen and tagged at the end of Nov 7. The first test-split run is on or after Nov 9.


## Status

Per the PRD, a Python skeleton (ingest, chunk, extract, verify, SQLite store, CSV export, mock provider, 10 passing tests) exists but **is not in this repo yet** (there is no `src/` folder yet). Not yet built: Streamlit screens, accept/remove actions, CUAD loader and evaluation script. No real model call has been made, so cost and latency are unmeasured.

Setup and run instructions will be added once the code is added.
