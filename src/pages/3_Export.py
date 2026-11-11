"""Export: the table that will be in the CSV, checked before it is downloaded. The preview is read from the very text the
download button hands out, so what is shown is what is saved. Nothing here changes the review."""
import csv
import html
import io

import streamlit as st

from clause_review.export import csv_text, file_stem, questions_csv_text
from clause_review.review_view import overview_stats, run_when
from clause_review.view import load_results
from common import get_store, new_review_button, refresh_corner, resume_latest
from theme import apply_theme, brand, export_link, kpi_row, marquee, nav_gap, views

st.set_page_config(page_title="Clautra · Export", page_icon="static/brand/clautra-mark-transparent.png", layout="wide")
apply_theme(st)
marquee(st)
store = get_store()

with st.sidebar:
    brand(st)
    views(st)
    nav_gap(st)
    new_review_button(st)
    export_link(st)

res = resume_latest(st, store)
if not res:
    st.info("There is nothing to export yet. Start a review from the Overview first.")
    st.page_link("app.py", label="Go to the Overview", icon=":material/grid_view:")
    st.stop()

refresh_corner(st)
docs = load_results(store, res["pid"], res["categories"])
stats = overview_stats(docs, list(res["categories"]))
text = csv_text(store, res["pid"])
rows = list(csv.DictReader(io.StringIO(text)))
gap_rows = [r for r in rows if r["quote"].startswith("[")]
passages = [r for r in rows if not r["quote"].startswith("[")]
unchecked = sum(1 for d in docs for c in res["categories"] if d["categories"].get(c) != "Found" and not d["reviewed"].get(c))

st.markdown('<div class="hero"><div class="eyebrow">Clautra &nbsp;/&nbsp; Export</div><h1>Export</h1>'
            '<p class="tag">Check the table, then download it.</p><hr class="rule"></div>', unsafe_allow_html=True)
saved = store.run_for_project(res["pid"])  # the review's own name, given when it was started: it names the files too
stem = file_stem(saved["name"]) if saved else "clause_review"
if saved:
    st.markdown(f'<div class="rv-context"><span class="rv-eyebrow">Exporting</span><span class="rv-name">{html.escape(saved["name"])}</span>'
                f'<span class="rv-meta">{len(docs)} contract{"s" if len(docs) != 1 else ""} · run on {html.escape(run_when(saved["created"], with_time=True))}'
                f' · saved as {html.escape(stem)}.csv</span></div>', unsafe_allow_html=True)

kpi_row(st, [(len(passages), "Passage" if len(passages) == 1 else "Passages", f'{sum(1 for r in passages if r["found_by"] == "Clautra")} by Clautra · {sum(1 for r in passages if r["found_by"] == "Reviewer")} by reviewer', False),
             (stats["pending"], "Passage not yet reviewed" if stats["pending"] == 1 else "Passages not yet reviewed",
              "saved as pending" if stats["pending"] else None, stats["pending"] > 0),
             (stats["waiting"], "Question without an answer" if stats["waiting"] == 1 else "Questions without an answer",
              "the answer column stays empty" if stats["waiting"] else None, stats["waiting"] > 0),
             (len(gap_rows), "Gap" if len(gap_rows) == 1 else "Gaps", f"{unchecked} not checked yet" if unchecked else "all checked", unchecked > 0)])

# what to look at before downloading: each line says what the file will contain, none of them stops the download
notes = []
if stats["pending"]:
    notes.append(f'{stats["pending"]} {"passage is" if stats["pending"] == 1 else "passages are"} still waiting for review and will be saved as pending.')
if stats["waiting"]:
    notes.append(f'{stats["waiting"]} {"question has" if stats["waiting"] == 1 else "questions have"} no answer from the Senior Lawyer yet.')
if unchecked:
    notes.append(f'{unchecked} {"gap has" if unchecked == 1 else "gaps have"} not been checked by you. Gaps are listed as "Not found, review required".')
if notes:
    st.warning("Before you download:\n\n" + "\n".join(f"- {n}" for n in notes))  # no buttons: each person goes back to their own page from the sidebar

FILTERS = ["All rows", "Found by Clautra", "Found by reviewer", "Accepted", "Not yet reviewed", "Removed", "Gaps", "Has a question"]
view = st.pills("Show", FILTERS, selection_mode="single", default="All rows", key="ex_filter", label_visibility="collapsed") or "All rows"
shown = {"All rows": rows,
         "Found by Clautra": [r for r in passages if r["found_by"] == "Clautra"],
         "Found by reviewer": [r for r in passages if r["found_by"] == "Reviewer"],
         "Accepted": [r for r in passages if r["review"] == "accepted"],
         "Not yet reviewed": [r for r in passages if r["review"] == "pending"],
         "Removed": [r for r in passages if r["review"] == "removed"],
         "Gaps": gap_rows,
         "Has a question": [r for r in passages if r["question"]]}[view]
st.caption(f"{len(shown)} of {len(rows)} rows shown. The download always has every row, exactly as listed here.")
st.dataframe(shown, use_container_width=True, hide_index=True, height=420, column_config={
    "document": st.column_config.TextColumn("Contract", width="medium"),
    "category": st.column_config.TextColumn("Clause", width="small"),
    "quote": st.column_config.TextColumn("Quote", width="large"),
    "page": st.column_config.TextColumn("Page", width="small"),
    "review": st.column_config.TextColumn("Review", width="small"),
    "question": st.column_config.TextColumn("Question", width="medium"),
    "answer": st.column_config.TextColumn("Answer", width="medium"),
    "found_by": st.column_config.TextColumn("Found by", width="small"),
})

d1, d2, _ = st.columns([1.3, 2, 2])
d1.download_button("Download CSV", text, file_name=f"{stem}.csv", mime="text/csv", type="primary", icon=":material/download:",
                   use_container_width=True, key="ex_csv")
if stats["waiting"] or stats["answered"] or any(f["question"] for d in docs for f in d["findings"]):
    d2.download_button("Download the questions only", questions_csv_text(store, res["pid"]), file_name=f"{stem}_questions.csv",
                       mime="text/csv", use_container_width=True, key="ex_q")
