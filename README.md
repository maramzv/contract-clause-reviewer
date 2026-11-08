# Contract Clause Extraction and Review

A web app that turns a batch of commercial contracts into a first-pass clause review table. Every finding shows the exact contract wording and its page. Every category the tool could not find is flagged for human review instead of being left blank.

**Owners:** Kerrian Gordon and Mara Munoz

The source of truth is the [final PRD](docs/02-prd/FINAL%20-%20Contract%20Clause%20Extraction%20and%20Review%20-%20%20PRD%20-%20Kerrian%20Gordon%20%26%20Mara%20Munoz.md). This README summarizes it and the code in `src/`. If they disagree, the PRD wins.

## Who did what

**Kerrian Gordon: the build and the evaluation design**
- The PRD's later updates and the scoring rule (pull requests #3 and #7).
- The Python package in `src/`: ingest, chunk, extract, verify, store, export, the model providers with a spend limit and cache, and its tests (#1).
- The Streamlit review screen, with accept, remove and restore, and the CSV download (#1, #2).
- The CUAD loader and evaluation script, with a regex-only baseline (#6).
- The written clause definitions and the answer-key design.

**Mara Munoz: research, documentation, design and the answer-key check**
- The assignment breakdown and the research: the job-description analysis and early design notes (`docs/00-assignment/`, `docs/01-research/`).
- This README and the repo setup: the `main` and `developer` branch workflow, and reviewing and merging pull requests (#1 to #7).
- The intro slideshow at `intro/`, with the project name and tagline (#4).
- UI design work for the review screens: a clickable prototype, a UI inventory and a plain-English walkthrough. These are kept locally for now and are not in the repo.
- The answer-key check: set up the test materials, read the contracts and the clause definitions, and signed off the definitions (`docs/03-tests/`). The marks for the 10 test contracts were produced by an AI model (Claude) from those contracts, not marked independently by a person, so the check is not an independent human check.

**Both:** the original PRD, owned by Kerrian and Mara together.

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
3. **Extract:** one model call per chunk returns category and exact quotation as JSON. The prompt lists, for each category, what counts and what does not (worded from the approved Clause Definitions). A keyword (regex) pass also finds candidate sentences, but its findings are kept only for a category where the model found nothing in that contract, so a model miss can still surface a candidate for review. Responses are cached by a hash of provider, model and prompt.
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

**Score it against CUAD** (from `src/`; needs the CUAD files `CUADv1.json` and `test.json` from the CUAD release, which stay on your machine and are not in this repo):

```
python -m clause_review.evaluate --cuad CUADv1.json --test test.json --baseline            # regex pass only, no model, free
python -m clause_review.evaluate --cuad CUADv1.json --test test.json --limit 20 --seed 1   # uses CLAUSE_PROVIDER
```

By default it scores the 408 development contracts. The 102-contract test split is refused unless you add `--allow-test`. It was run once, on Nov 8, after the freeze (git tag `freeze-2026-11-08`); see Results below, and do not tune against it. Paid model responses are kept in `--cache`, so a rerun does not pay again.

**Settings** (copy `.env.example` to `.env`; the app, the command line and the evaluation script read it automatically, and a variable you have already exported wins over the file. It is git-ignored, so never commit a real key):

| Variable | What it does |
|---|---|
| `CLAUSE_PROVIDER` | `mock` (default), `anthropic` or `local` |
| `ANTHROPIC_API_KEY` | Needed only for `anthropic` |
| `CLAUSE_MODEL` | Model name; the code defaults to `claude-sonnet-5-5` |
| `CLAUSE_WORKERS` | Parallel model calls (1 = one at a time) |
| `CLAUSE_BUDGET_USD`, `CLAUSE_PRICE_IN`, `CLAUSE_PRICE_OUT` | Spend limit. All three are needed together, and prices come from the price list. None are built in. |
| `CLAUSE_LOCAL_URL` | Address of the local model server, used when `CLAUSE_PROVIDER=local` |
| `CLAUSE_DB` | SQLite file for the review screen (default `review.db`) |

More detail, and the assumptions that are tested vs. still unmeasured, are in [src/README.md](src/README.md).

## Data and privacy

Evaluation and demos use **public contracts from CUAD** (510 contracts, 41 categories, CC BY 4.0). Real deal contracts should not be sent to a hosted model. The database stores the full text of every uploaded contract, so use public contracts only. Development uses 408 CUAD contracts. The 102-contract test split stays untouched until the answer key is frozen.

## Evaluation (after the build window)

| Goal | Target |
|---|---|
| Recall per category on the 102 test contracts (a match needs overlap ÷ union ≥ 0.5) | Average ≥ 0.80 |
| Precision after verification, compared against a regex-only baseline | Average ≥ 0.70, and F1 at least 10 points above baseline |
| Time saved, in a counterbalanced pilot with ≥ 2 reviewers | Median per-contract time at least 30% lower, with no more missed clauses |
| Processing time for the 30 largest test contracts (empty cache) | ≤ 30 minutes |

**How a match is counted:** a predicted passage matches a labeled one when their overlap divided by their union is at least 0.5 (Jaccard, the measure CUAD's own evaluation uses). Each labeled passage matches at most one prediction. The evaluation also prints a lenient secondary figure (overlap ÷ the shorter passage ≥ 0.5); the target above uses the Jaccard rule. Counts are pooled over contracts per category, and the headline is the average of the five categories. A contract the model fails on is counted and left out, never scored as empty.

The answer key, written category definitions and extractor prompts were frozen on Nov 8, 2026 and tagged `freeze-2026-11-08` (commit d717d6f).

### Results on the 102 test contracts (one run, frozen code, Claude Sonnet 5.5)

Run on Nov 8 after the freeze tag was pushed, a day earlier than the schedule's Nov 9. The freeze came first, so no test result could have influenced the frozen code.

| Category | Precision | Recall | F1 | Right / predicted / labeled |
|---|---|---|---|---|
| Assignment | 0.68 | 0.67 | 0.68 | 92 / 135 / 137 |
| Change of Control | 0.44 | 0.52 | 0.47 | 32 / 73 / 62 |
| Termination for Convenience | 0.69 | 0.71 | 0.70 | 29 / 42 / 41 |
| Renewal | 0.60 | 0.84 | 0.70 | 26 / 43 / 31 |
| Governing Law | 0.86 | 0.96 | 0.91 | 86 / 100 / 90 |
| **Average of five** | **0.65** | **0.74** | **0.69** | |

Lenient secondary measure: average precision 0.69, recall 0.78, F1 0.73. No contract failed. 95% ranges for the average (resampling the 102 contracts): precision 0.57 to 0.74, recall 0.68 to 0.80, F1 0.62 to 0.76.

| Target | Result |
|---|---|
| F1 at least 10 points above the regex-only baseline | Met. Baseline F1 on the same contracts is 0.42, so the gain is about 27 points (95% range 0.21 to 0.32). The regex pass alone with its final, tighter patterns scores 0.49. |
| Average recall at least 0.80 | Not met: 0.74 (lenient 0.78). Only Renewal and Governing Law reach 0.80. |
| Average precision at least 0.70 | Not met: 0.65 (lenient 0.69); the range reaches 0.74, so a small shortfall cannot be ruled out as noise. |
| Processing time, 30 largest test contracts (empty cache) | All 102 contracts took 14 min 40 s with 4 parallel workers, so any 30 of them take less. Inferred, not timed separately. |

**Cost and speed:** the test run used 2,096 model calls and cost $8.85 (about $0.09 per contract) at $2 / $10 per million input / output tokens. A 60-contract development run cost $6.09 (about $0.10 per contract).

**How the extractor was tuned (development contracts only):** the first real-model run on 60 development contracts gave average F1 0.53. The keyword pass turned out to supply many wrong findings, so it became a backstop (0.58). The prompt then listed what counts and what does not (0.66), and the Change of Control and Renewal keyword patterns were tightened (0.71 on those 60). On 40 fresh development contracts the final code scored 0.64, so about 7 points of the gain were specific to the tuning contracts. The test split was not used for any of this.

**Read these numbers with care:**
- CUAD leaves some real clauses unlabeled and our Assignment definition is narrower than CUAD's, so precision is understated by an unknown amount.
- Change of Control is the weakest category (F1 0.47).
- The answer-key check is limited: the marks on the 10 contracts were produced with AI, not by an independent human, and 3 contracts were hand-marked by one reviewer. Ten span or label differences have not been adjudicated, and the scores use the CUAD labels as published.
- The reviewer pilot and practitioner interviews have not been done, so the time-saved goal and the pain point are untested.
- Three correct model quotes in 60 development contracts were dropped because page-break filler sits inside the sentence; this is not fixed.

### What we would change next (not done, on purpose)

No change was made after the test run, so the frozen result stays clean. The errors below come from 100 development contracts (replayed from cached model replies), not from the test split.

- **Assignment** (development precision 0.71, recall 0.68; 41 of 128 labeled spans missed). CUAD labels sentences that make a prohibited assignment void or a breach, for example "Any purported assignment in violation of this paragraph shall be void". The model often misses them. Our "does not count" line about what happens after a transfer may be steering it away; that cause is not proven. Fix: count such sentences.
- **Termination for Convenience** (precision 0.66, recall 0.78). CUAD labels without-cause rights that end only part of the deal, such as a license, a scope of work or a fund ("We will have the right to terminate the Ad Fund by giving you thirty (30) days' advance written notice"). Our wording says "end the agreement". Fix: count a without-cause right to end part of the deal.
- **Change of Control** (precision 0.35, recall 0.53). CUAD's labels include triggers such as a party ceasing to own shares and assignment by operation of law, and the model's wrong findings include definitions and sentences such as "a change of control shall not be considered an assignment". CUAD's labeling is inconsistent here, so we expect little room to improve.
- **Verification:** a correct model quote fails the word-for-word check when page-break filler (a line of dashes, a "Source:" footer) sits inside the sentence. Fix: ignore that filler when matching.

Either definition change edits the signed Clause Definitions, so it needs approval, a new version tag, and a check on development contracts nobody has looked at. The test result would still belong to the frozen version; running a changed version on the test split again would be exploratory and should be reported that way.

## Status

**Built:** upload, category choice, findings with quotation, page and category status, failed files listed with the reason, accept/remove/restore, CSV download, the model providers with a spend limit and response cache, the CUAD loader and evaluation script (with a regex-only baseline, development split by default), and 57 passing tests (offline, on small invented files and the mock provider).

**Not built yet:** marking a category as reviewed (P1). The regex-only baseline (average precision 0.48, recall 0.52, F1 0.42 on the 408 development contracts) and the real-model run on the 102 test contracts are done; results are above.

## Repo layout

```
docs/00-assignment/   the assignment breakdown
docs/01-research/     job descriptions and early design notes
docs/02-prd/          the final PRD (source of truth)
docs/03-tests/        materials for the answer-key check (test contracts, marking sheet, definitions)
intro/                the intro slideshow (open intro/index.html)
src/                  the app, the clause_review package and tests
```
