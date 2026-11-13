# Speaker notes

One section per slide, in deck order.

## Slide 1: jd

About 30 seconds. We built for junior associates and contracts paralegals. Real postings say they review contracts for assignment and change of control during due diligence. Our reading of what that reveals: the same clause types searched in every contract, results copied into a table by hand, and no way to tell a missing clause from a missed one. That second layer is our hypothesis, not something the postings state.

## Slide 2: address

About 25 seconds. Three promises. It finds the clause. It shows the exact words and the page, and a quotation is shown only if it is found word for word in the contract. And it never hides a gap: a category with nothing verified is flagged for the reviewer, never left blank. It does not interpret clauses. The lawyer decides what each one means.

## Slide 3: workflow

About 30 seconds, and the demo video shows this. Before: Maya, a junior associate, searches 30 contracts for five clause types by hand, copies quotations and pages into a spreadsheet, and cannot tell whether a blank means absent. With the tool: she uploads all 30 once, reads one table, checks each quotation at its page, and searches by hand only the flagged gaps. Then she exports a CSV for her senior lawyer. We did not measure the time saved.

## Slide 4: architecture

About 35 seconds. Six steps. Ingest reads the PDF page by page. Chunk cuts it into 3,000-character windows. Extract is the only AI step: one Claude call per chunk proposes the category and the exact quotation. Verify is plain code: any quotation not found word for word in the contract is dropped. Store keeps findings and gaps in a local SQLite file. Review is the screen where Maya accepts or removes findings and exports the CSV. The model proposes, code decides.

## Slide 5: results

About 25 seconds. We tested once on 102 held-out contracts from the public CUAD dataset. F1 is 69 percent against 42 percent for a keyword baseline, which meets our target of ten points above. Precision is 65 percent against a target of 70, and recall is 74 percent against a target of 80, so both missed and we say so. Processing time meets the target by inference. The reviewer pilot was not run, so time saved is untested. Thank you.

