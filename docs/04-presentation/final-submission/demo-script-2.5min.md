# Demo video script: 2.5 minutes

Record your screen with narration. Run the app from the `src` folder (`streamlit run app.py`) with `CLAUSE_PROVIDER=anthropic` in `.env` so it uses the real model. Dev mode off. Do one full practice run first.

**Before you press record**
- Run the contracts you plan to show once, so you know what each finds and that the key works (about 7 cents per contract).
- Close other windows and notifications. Browser zoom 110 to 125 percent so the text is readable in the video.
- Start on an empty screen: no saved run open.
- Have `clause_review.csv` from an earlier run ready to open (Numbers, Excel or a text editor).

| Time | On screen | Say |
|---|---|---|
| 0:00 to 0:15 | The home screen. Point at the five clause categories in the sidebar. | "This is Contract Clause Review. Maya, a junior associate, has a batch of contracts and needs five clause types from each: assignment, change of control, termination for convenience, renewal and governing law." |
| 0:15 to 0:40 | Pick two sample contracts (Strategic Alliance Agreement plus one short one). Click Run review. The progress bars move. | "She uploads them once, or picks bundled public contracts. The model proposes quotations for each clause, and the code checks every quotation word for word against the contract." |
| 0:40 to 1:10 | Results appear: the three tiles. Open the first contract. Show a Found category with its quotation and page. | "Each Found category shows the exact words and the page, so she can check the wording in seconds." |
| 1:10 to 1:30 | Scroll to a category marked "Not found, review required". | "When nothing is verified, the category is flagged for her to search by hand. An empty result never proves the clause is absent, and the tool never leaves it blank." |
| 1:30 to 1:55 | Click Accept on a correct finding. Click Remove on one. If it was the only finding in the category, show it go back to Not found. | "She accepts what is right and removes false matches. If she removes every finding in a category, it goes back to Not found, so a removal never reads as a confirmed absence." |
| 1:55 to 2:15 | Click Download CSV. Open the file: one row per finding, the removed row marked, the bracketed gap rows. | "She exports a table for her senior lawyer: contract, category, exact quotation, page and review state. Removed findings stay in the file, marked removed." |
| 2:15 to 2:30 | Back on the app. Optionally open Saved runs. | "On 102 held-out contracts it scored F1 0.69 against 0.42 for keyword search. We did not measure time saved. Thank you." |

**Tips**
- If the run takes longer than 25 seconds, start it, say your lines over the progress bars, and cut the wait when you edit. Or use Saved runs, then Replay at 20x: it plays a saved run with no model calls.
- Use a short contract for the Remove step so it is easy to see.
- Keep to about 330 words. Read the table at a natural pace and time yourself.
