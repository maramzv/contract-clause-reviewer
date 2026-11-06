# Contract clause review: skeleton

Pipeline: ingest -> chunk -> extract (regex + LLM) -> verify (exact quote) -> SQLite -> CSV.

    pip install pypdf pytest streamlit   # anthropic is optional
    python -m pytest -q               # runs offline with the mock provider
    python -m clause_review.cli demo review.db out.csv samples/sample_contract.txt
    streamlit run app.py              # review screen: upload, choose categories, see findings (mock provider by default)
    CLAUSE_PROVIDER=anthropic ANTHROPIC_API_KEY=... python -m clause_review.cli ...   # hosted
    CLAUSE_PROVIDER=local CLAUSE_LOCAL_URL=... python -m clause_review.cli ...        # local model

Parallel calls and a spend limit (hosted model):

    CLAUSE_WORKERS=10 CLAUSE_BUDGET_USD=35 CLAUSE_PRICE_IN=<USD per million input tokens> \
    CLAUSE_PRICE_OUT=<USD per million output tokens> CLAUSE_PROVIDER=anthropic python -m clause_review.cli ...

The run stops when the budget is reached (it can overshoot by up to CLAUSE_WORKERS in-flight calls). Every paid
response is saved to the database at once, so a rerun does not pay for them again. Take the prices from the price list;
none are built in.

CUAD labels were checked against CUADv1.json (see categories.py). The official test split (102 contracts) is the
held-out set.

## What is built

Upload, category choice, findings with quotation, page and category status, failed files listed with the reason,
Accept, Remove and Restore on each finding, and a CSV download (`app.py`, `clause_review/view.py`). The screen runs on
whichever provider `CLAUSE_PROVIDER` selects; the default is the offline mock, and the screen says so.

TODO: mark a category as reviewed. The evaluation runs on the development split only so far, and a real-model run has not been made yet.

## Assumptions and limits

Status: **tested** = a test covers it; **observed** = seen when running the app, no test; **chosen** = a design choice
not yet measured; **unmeasured** = depends on the real model.

- Chunks are about 3,000 characters with 300 overlap, cut at a paragraph or sentence boundary when one is available.
  Offsets are tested; the sizes are **chosen**.
- One model call per chunk asks for all selected categories at once, to keep the number of calls down. Effect on recall:
  **unmeasured**.
- A quotation counts only if it is found word for word after whitespace is collapsed and is at least 15 characters.
  **Tested.** Where quotations in one category overlap, the model's quotation is kept over a regex one, and among
  quotations from the same source the tightest is kept. **Tested** on a wrapped clause; the effect on recall is
  **unmeasured**.
- A regex hit becomes the whole sentence around it, so a clause that a PDF wraps over several lines is one quotation.
  A sentence ends at a blank line, or at . ! ? followed by a capital letter, digit, bracket or quote, so an
  abbreviation such as "Inc. Shall" can cut a sentence short. A "sentence" over 1,000 characters falls back to the
  line. **Tested** on synthetic text; real contracts are untested.
- Pages come from pypdf's per-page text; a text file is one page; section headings are not detected. **Observed** on a
  generated two-page PDF only; real contracts are untested.
- A file with fewer than 50 characters of extractable text (for example a scanned PDF) is stored as failed, and every
  selected category shows "Failed to process". OCR is out of scope. **Tested.**
- If the model's reply is not a JSON list, that chunk adds no model findings and any category left empty shows
  "Not found, review required". It is flagged, not hidden, but the cause is not shown. **Unmeasured.**
- Findings start as `pending`; Accept sets `accepted`, Remove sets `removed`, Restore sets `pending`. A removed finding
  stays in the database and on screen (struck through) so it can be restored, and the CSV leaves it out. If every
  finding in a category is removed, the category goes back to "Not found, review required", so removing a false match
  never reads as a confirmed absence. **Tested.**
- The database stores the full text of every uploaded contract. Use public contracts only.
- Each Run in the screen creates a new review named by the time of the run (the PRD's "one default review"). **Chosen.**
- The mock provider finds clauses with keyword rules. Results from it say nothing about model quality.

The PRD's technical section (section 4) describes the same pipeline for readers who do not use the code.

## Scoring against CUAD (development split)

```
python -m clause_review.evaluate --cuad CUADv1.json --test test.json --baseline          # regex pass only, free
python -m clause_review.evaluate --cuad CUADv1.json --test test.json --limit 20 --seed 1  # uses CLAUSE_PROVIDER
```

`CUADv1.json` and `test.json` come from the CUAD release (CC BY 4.0) and stay on your machine; nothing in the repository holds labels.
The default is the 408 contracts outside CUAD's test split. `--split test` is refused unless `--allow-test` is added; the plan is to leave
the test split untouched until the answer key, definitions and prompts are frozen (end of November 7).

A prediction matches a gold span when overlap divided by union is at least 0.5 (Jaccard, as in CUAD's own evaluation). Each gold span
matches at most one prediction. Counts are pooled over contracts per category, and the headline is the average of the five categories.
Contracts whose model call failed are counted and left out of the scoring, never scored as empty. Paid responses are kept in `--cache`.

Known limits: a quote that appears twice in a contract is located at its first occurrence, so a repeated boilerplate sentence can
miss its gold span; the 50% rule is Jaccard, which is stricter than "overlap by at least 50% of the gold span".
