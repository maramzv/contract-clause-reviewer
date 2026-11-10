# Speaker notes

One section per slide, in deck order.

## Slide 1: cover

A contract clause extraction and review tool for a junior associate (the persona Maya), evaluated on the public CUAD dataset. The five categories on the slide are the ones we mapped to CUAD labels. Project deadline: November 12, 2026.

## Slide 2: problem

The problem, as we framed it. Junior associates and contracts paralegals repeat the same work in diligence: find the same clause types, copy quotations and page references, and wonder whether an empty keyword search means the clause is truly absent. These pain points are hypotheses. No job posting says that finding clauses is the slow step, and we never measured the time saved. Maya is an illustrative persona, not an interviewed user.

## Slide 3: what

The user flow. Upload contracts and choose categories. The system finds candidate passages and keeps only quotations that appear word for word in the contract. Maya accepts, removes or restores each finding. The CSV leaves out removed findings, and every category without a verified finding appears as a bracketed row. The three states are what make a gap visible: a missing result is never treated as a confirmed absence.

## Slide 4: maya

The tool in Maya’s own working day, following the PRD’s first user journey. Her senior sends 30 contracts and asks for five items from each. She uploads them once and reads one table instead of searching 30 files five times. Every Found row has the exact wording and its page, so she can check it quickly. Every gap is visible, and she searches only those by hand. The senior lawyer receives the CSV and the contracts and decides what each clause means. Maya is an illustrative persona and the time saved has not been measured.

## Slide 5: guarantees

These are guarantees by construction. The verbatim check normalizes whitespace and requires at least 15 characters. They say nothing about whether the model found every clause: that is what the test results measure. They guarantee that what is shown is real contract wording, and that a gap is always visible to the reviewer.

## Slide 6: pipeline

The pipeline in the code. The keyword (regex) pass is a backstop: its findings are kept only for a category where the model found nothing in that contract, so a model miss can still surface a candidate for review. Model replies are cached by a hash of provider, model and prompt, so a re-run does not pay twice. Locations are PDF page numbers; a text file counts as one page.

## Slide 7: evaluation

CUAD: 510 public contracts, labeled for 41 clause types; we use five. 408 were used for development and 102 form the test split, which was refused by the script unless explicitly allowed. The test split was run once, on November 8, after the freeze tag was pushed. That was a day earlier than the schedule's November 9, and the PRD records it. Contracts where the model call failed would have been counted and excluded; none failed. Process note: the plan called for the answer-key disagreements to be settled before the freeze; they were not. See the answer-key slide.

## Slide 8: headline

Averages of the five categories, from pooled counts, scored with the Jaccard rule (overlap divided by union at least 0.5). The 95% ranges come from resampling the 102 contracts 2,000 times. The baseline gain is about 27 points, with a 95% range of 0.21 to 0.32. A more lenient measure (overlap divided by the shorter passage) gives precision 0.69, recall 0.78 and F1 0.73. No contract failed. Scored against CUAD labels as published.

## Slide 9: categories

Governing Law is the strongest category (F1 0.91). Change of Control is the weakest (F1 0.47). Only Renewal and Governing Law reach 0.80 recall. Right / predicted / labeled means: predictions that matched a label, total predictions, total labeled passages. Precision is understated by an unknown amount because CUAD leaves some real clauses unlabeled, and our Assignment definition is narrower than CUAD's.

## Slide 10: targets

One target met, two missed, one met by inference and one untested. The precision range reaches 0.74, so a small shortfall cannot be ruled out as noise. The processing-time target was about the 30 largest contracts with an empty cache; we ran all 102 in 14 minutes 40 seconds, so any 30 of them take less, but we did not time that subset separately. The reviewer pilot was not run because we could not find reviewers, so the time-saved goal is untested and we make no claim about it.

## Slide 11: tuning

Average F1 on 60 development contracts for the first four bars, then 0.64 on 40 development contracts nobody had tuned against. The keyword pass turned out to supply many wrong findings, so it became a backstop. Listing what counts and what does not in the prompt, worded from the signed clause definitions, was the biggest single gain. The drop from 0.71 to 0.64 on fresh contracts shows about 7 points of the gain were specific to the tuning contracts, which is why the test split result (0.69) is the number to trust.

## Slide 12: answer-key

Judged on Nov 9, after the freeze and the test run, which is not the order the evaluation plan set. Kerrian and Mara decided to keep the CUAD labels. The sensitivity check is a replay of the saved test run with the disputed spans removed from the key: F1 0.691 to 0.695, recall 0.738 to 0.745, precision unchanged at 0.655. It was not used to change anything.

## Slide 13: limits

What we do not claim. The scores are against CUAD labels as published. Precision is understated by an unknown amount. The answer-key check was not independent. The time-saved target and the pain point are untested, so we make no claim that the tool saves a reviewer time. The verification bug is known and not fixed, because fixing it after the test run would have broken the freeze.

## Slide 14: next

Not done, on purpose. The error analysis was replayed from cached model replies on 100 development contracts. Either definition change edits the signed Clause Definitions, so it needs approval, a new version tag, and a check on development contracts nobody has looked at. Running a changed version on the test split again would be exploratory and would have to be reported that way. The export item came from a demo run, not the evaluation: the CSV used to leave out removed findings. It was fixed on Nov 10 (export only; the findings and scores are unaffected) and checked on a mock run and one real-model run.

