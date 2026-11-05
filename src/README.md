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

Upload, category choice, findings with quotation, page and category status, and failed files listed with the reason
(`app.py`, `clause_review/view.py`). The screen runs on whichever provider `CLAUSE_PROVIDER` selects; the default is the
offline mock, and the screen says so.

TODO: accept and remove actions, CSV download button, CUAD loader, eval script. A real-model run has not been made yet.

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
- Findings start as `pending`; the planned states are `accepted` and `removed`, and the CSV leaves out `removed`.
  The actions that set them are not built.
- The database stores the full text of every uploaded contract. Use public contracts only.
- Each Run in the screen creates a new review named by the time of the run (the PRD's "one default review"). **Chosen.**
- The mock provider finds clauses with keyword rules. Results from it say nothing about model quality.

The PRD's technical section (section 4) describes the same pipeline for readers who do not use the code.
