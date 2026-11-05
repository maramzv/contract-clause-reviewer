 **CONTRACT CLAUSE EXTRACTION AND REVIEW**  
*Product Requirements Document: Net New Build*

**Build name:**  Contract Clause Extraction and Review

**Owner:**  Kerrian Gordon and Mara Munoz

**Date:**  November 5, 2026

**Build window:**  November 5 to 7, 2026 (three days). Project deadline: November 12, 2026\.

# **1\. PROBLEM**

**Pain (unvalidated):**  When Maya searches a contract for a clause and finds nothing, she cannot tell whether the clause is absent or her keywords missed it. In diligence review she repeats that search for every clause type in every agreement and copies quotations and page numbers into a table. Her senior lawyer then asks “where does the contract actually say that?” before trusting the table.

**Evidence so far:**  This pain is a hypothesis. It rests on job postings that describe the surrounding work: E-Space and LegalShield list turnaround time, consistent review processes and renewal tracking, and Pylon says contract review is a bottleneck for redlines at a startup. No posting says that finding clauses is the slow step or that an empty search leaves reviewers unsure. No contract reviewer has been interviewed yet. The questions for them are in section 6\.

### **Supporting Context (optional)**

* Maya, the junior associate this product is built around, is asked to review 30 customer and supplier contracts before an acquisition closes and to report which ones contain assignment restrictions or change-of-control provisions. Maya is an illustrative persona, not a documented customer case.

* Pain-related language in real postings: an [E-Space Contract Paralegal](https://jobs.lever.co/espace/59ffb796-535d-4f6e-95db-2146d36953d5) posting asks for tracking of contract volume, turnaround times and pipeline status, renewal deadlines, and escalation of non-standard NDAs and vendor terms. A [LegalShield (PPLSI) Paralegal](https://www.builtinboston.com/job/paralegal/11303138) posting, removed on October 20, 2026, asked for improved turnaround time, shorter cycle times, consistent review processes and monitored renewal deadlines. E-Space and LegalShield are in-house roles that state goals more than complaints, so they show what reviewers are held to, not how often it goes wrong. A [Pylon Legal & Contract Ops](https://joinrise.co/pylon/legal-contract-ops-i9id) posting states the problem directly: “We have a contract bottleneck problem” and “Every redline that sits too long kills a deal.” Its fit is limited: about 10 customer contract reviews a month, review of customer redlines instead of clause extraction for diligence, and no clause types named. A [Cantor Fitzgerald M\&A contract paralegal](https://www.goparalegals.com/jobs/539447438-it-contract-paralegal-mergers-and-acquisitions-at-cantor-fitzgerald) posting lists analyzing contracts for transferability and change of control, which matches two checklist categories, but it states no pain. Maya is a law-firm associate, so the fit still needs practitioner validation.

* Pain points to validate with contract reviewers: relevant language appears under “Miscellaneous” instead of an obvious clause heading; the same categories are searched in every agreement; quotations and page references are copied into a spreadsheet by hand; and an empty keyword search leaves the reviewer unsure whether the clause is missing.

* Labeled data exists for this task. The Contract Understanding Atticus Dataset (CUAD) contains 510 commercial contracts with more than 13,000 labels across 41 clause categories, released under a CC BY 4.0 license, so extraction accuracy can be measured instead of guessed.

## 1a. Opportunity

Give legal reviewers a first-pass clause table for a whole batch of contracts in minutes, where every finding links to the exact source wording and every gap is flagged for human review, so reviewers spend their time judging what the terms mean instead of searching and copying.

### **Market Opportunity**

* The same extract-and-organize task recurs across several roles: junior lawyers, paralegals and legal analysts, in-house counsel, contract managers, procurement teams and legal operations. A corporate contracts paralegal posting from ImmunityBio lists reviewing contracts for assignment and change-of-control provisions during due diligence (see Section 6).

* Market size is not quantified in this PRD. The project is validated instead by the accuracy and reviewer-time targets in Section 2d, and CUAD supplies the labeled data to measure accuracy from the first build.

* Established products such as Litera Kira already extract clauses for diligence at scale. This project is a class-scale build, and the Appendix explains how it differs.

## 1b. Users & Needs

**Primary user(s):**  Junior corporate legal associates, paralegals and legal analysts (Maya) who turn a batch of commercial contracts into an accurate review table with source references. They care about not missing a clause and about showing where each finding came from.

**Secondary users:**  Senior lawyers, who review the table and decide what each provision means for the deal. Contract managers and in-house counsel are later audiences.

### **Key User Needs**

As Maya, I need the same clause checklist applied to every contract in the batch because I cannot re-search each agreement by hand.

As Maya, I need each finding shown with the exact contract wording and its location (page number) because I must verify it quickly.

As Maya, I need a category with no result marked “not found, review required” because an empty keyword search does not prove the clause is absent.

As Maya, I need to accept or remove findings and export a reviewed table because the deal team needs a clean record.

As a senior lawyer, I need to see the passage behind every finding and any question Maya flagged because I decide what it means for the transaction.

# **2\. PROPOSED SOLUTION**

Contract Clause Extraction and Review is a web app that turns a batch of commercial contracts into a review table with source evidence. Maya creates a review, uploads the contracts and chooses a checklist of clause categories: assignment, change of control, termination for convenience, renewal and governing law. The system finds candidate passages, keeps only quotations that appear word for word in the contract, and shows each one with its location (page number), marking any category it could not find as “not found, review required.” Maya accepts or removes findings and exports the reviewed table, so she spends her time on what the terms mean instead of searching and copying.

**What changes for Maya:**  Today she runs keyword searches for five clause types in each of 30 contracts, copies each quotation and page into a spreadsheet, and treats an empty search as probably meaning the clause is not there. With the tool she uploads the 30 contracts once and gets one table in which every contract and category either has a verified quotation with its page or is marked Not found, review required. She checks the quotations against the contracts, removes false matches and exports the table. What she can show her senior lawyer is a table where every quotation is traceable to a page and every gap is visible. How much time this saves has not been measured: the build has not been timed on real contracts, and the reviewer pilot in the Evaluation plan tab is where it will be tested.

## 2a. Value Proposition

Junior legal associates and paralegals who struggle to find and record the same clause types across dozens of contracts, because wording and headings vary, use Contract Clause Extraction and Review, a web app that extracts clauses with their exact source text into a review table. Unlike keyword search and manual copying into a spreadsheet, it shows only quotations verified word for word against the contract and flags every category it could not find, aiming to cut the time reviewers spend searching and copying, without asking them to trust unverified output.

## 2b. Top 3 MVP Value Props

**The Vitamin**  *(must-have baseline)*:  Every selected clause category is checked in every uploaded contract, and each finding shows the contract name, exact quotation and location.

**The Painkiller**  *(solves the core pain)*:  Categories with no result are marked “not found, review required” instead of being left blank, so an empty search is never mistaken for an absent clause.

**The Steroid**  *(the magic moment)*:  Each finding shows its exact quotation and page, so “where does it actually say that?” is answered without searching the contract. Highlighting the passage in the full contract text is a P1 follow-up.

## 2c. Goals & Non-Goals

### **Goals**

* Give reviewers a first-pass clause table for a batch of contracts in minutes, with each finding traceable to its exact source wording.

* Find the checklist clauses reliably: high recall on the five checklist categories, measured against CUAD labels.

* Never show a quotation that is not in the contract, and never treat a missing result as a confirmed absence.

* Show that reviewers save time even after checking the output.

### **Non-Goals**

* Legal interpretation and risk scoring. The product finds and organizes wording; lawyers decide what it means.

* Scanned or image-only PDFs (OCR) and non-English contracts. These are flagged as failed to process.

* Drafting, redlining, negotiation and deadline reminders. Deferred; contract managers may need them later.

* Multi-user accounts, comment threads, production security and integration with document management systems.

* Policy comparison and the other audiences in the user spec (contract managers, procurement, legal operations). Deferred.

* Processing real client contracts with a hosted model. Demos and evaluation use public contracts.

* Tuning the extractor on the 102 contracts in CUAD's test split. Development uses only the other 408; the test split stays untouched until the answer key is frozen.

* Scoring notice of non-renewal (CUAD's Notice Period To Terminate Renewal label). Only the five mapped labels are scored; decided November 4, 2026 (see the Appendix).

## 2d. Success Metrics

| Goal | Signal | Metric | Target |
| :---- | :---- | :---- | :---- |
| Never show a quotation that is not in the contract | Every displayed quotation can be found in the source | Share of displayed quotations that appear word for word in the contract after whitespace normalization | 100% |
| Never treat a missing result as absence | Gaps and failures are always visible to the reviewer | Share of contract and category pairs with no verified finding that are labeled “not found, review required” or “failed to process” | 100% |
| Show a working end-to-end demo by November 7 | A reviewer can go from upload to a reviewed CSV in one session | Pass or fail demo run on 3 CUAD contracts: each P0 step in section 3 completed without manual fixes | All P0 steps completed on all 3 contracts |

Recall, precision, the time-saving pilot and the processing-time target are measured after the build and are defined in the Evaluation plan tab.

# **3\. REQUIREMENTS**

## User Journey 1: Maya, a junior associate, turning a batch of contracts into a reviewed clause table

**Context:**  This is the core workflow. We optimize for accuracy she can verify quickly: every finding traces to the contract text, and nothing is silently missing.

**Scenario:**  Maya's senior lawyer sends 30 contracts for diligence and asks for five items from each: assignment, change of control, termination for convenience, renewal and governing law. Within the P0 scope she works like this.

1. She opens the app, keeps all five categories selected and uploads the 30 files (PDF or text).  
2. The app reads each file. A file it cannot read, such as a scanned PDF, is listed as Failed to process with the reason, and Maya reviews it by hand.  
3. For every contract she sees each category with a status: Found, with the exact quotation and its page, or Not found, review required.  
4. She opens the contract at each quoted page and checks the wording. She accepts correct findings and removes false matches. A category whose findings are all removed goes back to Not found, review required.  
5. For each category marked Not found, review required she searches that contract herself, because an empty result is never treated as proof that the clause is absent.  
6. She downloads the CSV and sends it with the contracts to the senior lawyer.

**Sub-journey: Setting up a review**

* **\[P1\]**  User can create a review project and name it.

  * **\[P0\]**  User can upload multiple contracts (PDF or text) to one review.

  * **\[P0\]**  User can see which uploaded files could not be processed, with the reason.

  * **\[P0\]**  User can choose which clause categories to check: assignment, change of control, termination for convenience, renewal and governing law.

  * **\[P2\]**  User can add a custom category with a plain-language description.

**Sub-journey: Inspecting findings**

* **\[P0\]**  User can open any contract and see each finding’s exact quotation and location (page number).

  * **\[P1\]**  User can see each quotation highlighted in the full contract text.

  * **\[P0\]**  User can see each category’s status: found, not found (review required), or failed to process.

  * **\[P1\]**  User can keep reading one contract while the others are processed and see each contract’s status.

  * **\[P1\]**  User can filter findings by category or status.

  * **\[P2\]**  User can sort the contract list by number of unresolved categories.

**Sub-journey: Verifying, correcting and exporting**

* **\[P0\]**  User can accept a finding or remove a false match.

  * **\[P1\]**  User can mark a category as reviewed.

  * **\[P0\]**  User can export the reviewed table (contract, category, quotation, location, review state) to CSV.

  * **\[P1\]**  User can flag a finding with a question for the senior lawyer.

  * **\[P1\]**  User can add a passage the tool missed by selecting text in the contract.

  * **\[P2\]**  User can see how many findings were accepted or removed in a review.

## User Journey 2: Senior lawyer checking Maya’s table and deciding what matters

**Context:**  The senior lawyer decides what each provision means for the deal. We optimize for fast verification: any finding can be checked against the source without searching the contract separately.

**Scenario:**  The senior lawyer receives Maya's CSV and the 30 contracts. Within the P0 scope he works like this.

1. He opens the CSV in a spreadsheet. Each row is a finding with the contract, category, exact quotation, page and review state. A row in square brackets, such as \[Not found, review required\] or \[Failed to process\], marks a category nobody has confirmed.  
2. To check a finding, he opens the contract at the page given and finds the quotation word for word. The tool does not highlight it for him yet (P1).  
3. He filters the CSV by category to list the contracts with an assignment or change-of-control finding. The in-app list is P1.  
4. He messages Maya about each bracketed row and about any finding he doubts. Flagged questions inside the tool are P1.  
5. He decides what each clause means for the deal. The tool does not interpret clauses.

**Is the CSV enough in P0?**  Yes for verifying and for deciding what to follow up: every quotation can be checked against a page, and every gap is listed. It is not enough for reading Maya's questions next to the passage or for seeing the highlighted text in the contract, both of which are P1. Until those exist, questions go by message and he finds the passage by page number. The CSV also has a question column that stays empty until flagging is built.

**Sub-journey: Checking the reviewed table**

* **\[P0\]**  User can read each finding with contract name, category, exact quotation, location and review state in the exported table.

  * **\[P0\]**  User can see which categories are unresolved (not found, review required, or failed to process).

  * **\[P1\]**  User can open the review in the same app session and jump from a finding to its highlighted passage.

  * **\[P1\]**  User can read Maya’s flagged questions attached to the exact passage.

**Sub-journey: Deciding what needs attention**

* **\[P1\]**  User can list every contract with an assignment or change-of-control finding.

  * **\[P1\]**  User can see which contracts have no finding for a category and ask for a manual check.

  * **\[P1\]**  User can filter the table to flagged questions only.

# **4\. TECHNICAL APPROACH**

This section describes how the build is put together so that the P0 requirements in section 3 can be built and demonstrated inside the build window.

## 4a. Build window and plan

**Build window:** November 5 to 7, 2026 (three days). The project deadline is November 12, 2026\. Only the P0 requirements in section 3 are committed for the build window. P1 and P2 items are built only if P0 is finished and demonstrated; otherwise they belong to a later phase. The extractor is frozen at the end of November 7, 2026\. The evaluation and the reviewer pilot run after the freeze and are defined in the Evaluation plan tab.

**Starting point:** a Python skeleton already runs end to end on a mock model provider (ingest, chunk, extract, verify, SQLite store, CSV export) and has 10 passing tests. Not built yet: the Streamlit review screens, the accept and remove actions, the CUAD loader and the evaluation script. No call to a real model has been made, so tokens, cost and seconds per contract are not yet measured.

* **November 5:** Run the skeleton on 3 CUAD contracts with Claude Sonnet and record tokens, cost and time per contract (this needs the facilitator's API key and price list). Add the accept and remove actions to the store.  
* **November 6:** Build the Streamlit screens: upload, category choice, findings for each contract with quotation, page and status, accept or remove, and CSV download.  
* **November 7:** Rehearse the demo on 3 CUAD contracts, prepare the fallbacks in 4e, write the CUAD loader and evaluation script (these do not change the extractor and may finish after the freeze), and freeze and tag the version at the end of the day.

## 4b. Stack and hosting

* **Frontend:** Streamlit, in one Python process.  
* **Backend:** the clause\_review Python package (ingest, chunk, extract, verify, store, export), called directly by the Streamlit app. There is no separate API server.  
* **Database:** SQLite, one local file.  
* **Model:** Claude Sonnet through the facilitator's API key, read from an environment variable and never written to the database or the CSV. A mock provider runs offline for development and is the demo fallback. A local model is a stretch option only.  
* **Hosting:** the demo runs locally on one machine (Streamlit on localhost). Vercel is not used. Its functions do not share memory between instances, close long connections at a maximum duration (300 seconds on the Hobby plan) and offer no persistent file for SQLite, and running Streamlit there is unverified. Hosting is out of scope for the build window.

## 4c. Data flow, upload to export

1. **Upload.** The reviewer chooses the categories and uploads PDF or text files in Streamlit. The build creates one default review for the session.  
2. **Ingest.** pypdf reads the text of each PDF page and records where each page starts, so any character position maps to a page number. A file that cannot be opened or has no extractable text (a scanned PDF) is stored as Failed to process with the reason.  
3. **Chunk.** The text is split into windows of about 3,000 characters with 300 characters of overlap, cut at a paragraph or sentence boundary where one is available. Each chunk keeps its position in the contract.  
4. **Extract.** A regex pass finds candidate sentences for each category. Then one model call per chunk asks for all selected categories at once and must return a JSON list of category and exact quotation. Responses are cached by a hash of provider, model and prompt, so a rerun does not pay again.  
5. **Verify.** A quotation is kept only if it is found word for word in the contract after whitespace is collapsed and is at least 15 characters long. Its start position gives the page. Quotations that cannot be found are dropped and never shown. Overlapping findings in the same category are merged, keeping the shortest.  
6. **Store.** Findings and category statuses are written to SQLite. A category with no verified finding is set to Not found, review required.  
7. **Review.** The reviewer sees each finding with its quotation, page and status, and accepts or removes it.  
8. **Export.** The reviewed table is exported to CSV with contract, category, quotation, location, review state and note.

Locations are page numbers taken from the PDF. A text file counts as one page. Section headings are not detected.

## 4d. Data model (SQLite)

* **Project:** id, name, created time.  
* **Document:** id, project, file name, the full extracted text, status and error message.  
* **Finding:** id, document, category, exact quotation, start and end character positions, page, source (regex or model), review state (pending, accepted or removed) and the reviewer's note or question.  
* **CategoryStatus:** document, category, status (Found, Not found review required, or Failed to process) and a reviewed flag.  
* **LLMCache:** a hash key and the raw model response.

## 4e. Technical risks and fallbacks

* **PDF text quality.** Scanned PDFs have no text, and two-column layouts or odd line breaks can stop a quotation from matching. Scanned files are reported as Failed to process (OCR is a non-goal). A quotation that does not match is dropped, so its category shows Not found, review required instead of a wrong quote. Fallback: the demo uses CUAD contracts that extract cleanly, checked in advance.  
* **Long contracts.** A 100-page contract is about 100 chunks or more, and each chunk is one model call. Fallback: CLAUSE\_WORKERS runs calls in parallel and the cache makes a rerun free. The 30-minute target for large batches is tested in the evaluation, not promised for the demo.  
* **Cost and latency.** Cost per contract is not yet measured. A run stops at a set budget (CLAUSE\_BUDGET\_USD, with the price per million tokens), overshooting by at most the number of calls in flight, and the evaluation limit is \$40. Fallback: measure 3 contracts on November 5 and size the evaluation from that.  
* **Model API fails or rate-limits during the demo.** Fallback: rerun from the cache of an earlier run on the same contracts, which needs no network. The mock provider is the last resort and is labeled as a mock run.  
* **Model paraphrases instead of quoting.** Verification drops the quotation. The cost is lower recall, which the evaluation measures.

# **5\. APPENDIX**

**Build skeleton:** Python package with ingest, chunk, extract, verify, SQLite store, CSV export and a CUAD-style scorer. It runs offline with a mock model provider.

**Dataset:** CUAD (CC BY 4.0, 510 contracts, 41 categories).

**Data handling:** Real deal contracts should not go to a hosted model. Demos and evaluation use public contracts (CUAD), and the write-up says so.

**Competitive context:** Established tools already extract clauses for diligence. [Litera Kira](https://www.litera.com/products/kira) links each answer to the source contract and states 95%+ precision on target provisions (a vendor claim we have not verified). [Spellbook](https://spellbook.com/automated-legal-contract-analysis-software) reviews contracts and suggests redlines inside Word. Luminance is used by law firms for M\&A due diligence, for example [Houthoff](https://houthoff.com/insights/news/houthoff-buruma-uses-luminances-ai-to-streamline-ma-due-diligence). This project does not compete on features or scale. The differences to test are verbatim verification of every quotation, an explicit “not found, review required” state, and a measured evaluation on public CUAD data.

**Evaluation plan:** The answer key, written definitions, freeze, disagreement handling, model and spending limit, and CUAD label mapping are in the Evaluation plan tab.

—

## 6\. Job Description Evidence

Added November 3, 2026\. Three real employer postings connect the proposed users and workflow to stated job responsibilities. They support role fit; they do not establish how often reviewers miss clauses, how much time extraction takes, or whether this product will save time. Maya remains an illustrative persona. Four further postings, added November 4, 2026, are listed below: Cantor Fitzgerald adds a clause-level duty, and E-Space, LegalShield and Pylon add pain-related language.

### **Junior corporate associate roles**

**Andrews Myers**

**Role:** Corporate Transactional Associate (First-Year / Junior). The posting targets recent law graduates or first-year attorneys in its corporate and M\&A practice.

**Relevant responsibilities:** Conduct legal due diligence and prepare detailed diligence reports; draft and review NDAs, disclosure schedules and closing documents; support transaction closings; and work on commercial agreements.

**Connection to this PRD:** This is the closest match to Maya’s senior-supervised acquisition review. The product would support finding and organizing passages for a diligence table. The JD does not explicitly require automated extraction or establish that searching is the main bottleneck.

[Employer posting — Andrews Myers](https://www.andrewsmyers.com/about-the-firm/careers/general-inquiries/)

**Klehr Harrison Harvey Branzburg**

**Role:** Junior Corporate Associate. The posting typically seeks 2–3 years of corporate or transactional experience, with certain other relevant experience considered.

**Relevant responsibilities:** Draft and review corporate agreements, resolutions and transaction documents; conduct due diligence; assist with transaction closings; and support mergers and acquisitions.

**Connection to this PRD:** Confirms that reviewing agreements and conducting diligence are explicit junior-associate responsibilities. Extracted quotations and source references could support this work; that benefit still needs practitioner validation.

[Employer posting — Klehr Harrison](https://klehr.com/careers/junior-corporate-associate/)

### **Corporate paralegal evidence**

**ImmunityBio**

**Role:** Paralegal, Corporate Contracts. This is a corporate paralegal role and is not explicitly identified as junior.

**Relevant responsibilities:** Support commercial contract management, administration, review, drafting and negotiation; support M\&A, financing and other strategic transactions; and review contracts for assignment, change-of-control and other pertinent provisions during due diligence.

**Connection to this PRD:** This is the most direct match to the proposed assignment and change-of-control checklist. It supports including corporate contracts paralegals alongside junior legal associates as primary users.

**Source limitation:** These responsibilities were available in an indexed copy of the employer’s Workday posting. The live page did not expose readable text during retrieval, so confirm the full posting and requirements before treating it as a currently open vacancy.

[Employer posting — ImmunityBio](https://nant.wd5.myworkdayjobs.com/en-us/immunitybio/job/paralegal--corporate-contracts_r3103)

**Cantor Fitzgerald**

**Role:** IT Contract Paralegal, Mergers and Acquisitions. The listing is dated June 10, 2026 and does not say whether the role is still open. It is not explicitly junior.

**Relevant responsibilities:** One listed responsibility is “analyzing vendor/customer contracts for transferability, change of control, and IP ownership issues.”

**Connection to this PRD:** This is a second direct match to the assignment (transferability) and change-of-control categories, alongside ImmunityBio. The posting states no pain, volume or turnaround problem, and its contracts are IT vendor and customer agreements.

**Source limitation:** The text comes from a GoParalegals copy of the posting. Confirm it with the employer before treating it as a current vacancy.

[Posting copy — Cantor Fitzgerald (GoParalegals)](https://www.goparalegals.com/jobs/539447438-it-contract-paralegal-mergers-and-acquisitions-at-cantor-fitzgerald)

### **Pain-related language**

Added November 4, 2026\. These three postings concern turnaround, renewals and escalation. E-Space and LegalShield state goals and duties, not complaints, so they show what reviewers are held to and not how often it goes wrong. Pylon states the problem directly, but for a different kind of review (see its fit limits).

**E-Space**

**Role:** Contract Paralegal (also listed as Contract Specialist or Contract Paralegal). This is an in-house role and is not explicitly junior.

**Relevant responsibilities:** Handle routine contract management and resolve routine matters independently; route non-standard NDAs to Corporate Counsel and escalate non-standard or higher-risk vendor provisions; track key dates, renewal deadlines, expirations and obligations and flag upcoming action items; and track and report on contract volume, turnaround times and pipeline status.

**Connection to this PRD:** Supports the renewal category and the practice of escalating non-standard provisions to a senior lawyer. The posting asks for volume and turnaround to be tracked and for contracting efficiency to improve. It does not say that reviewers struggle to find clauses or that review is slow.

[Employer posting — E-Space](https://jobs.lever.co/espace/59ffb796-535d-4f6e-95db-2146d36953d5)

**LegalShield (PPLSI)**

**Role:** Paralegal. This is an in-house commercial contracts role and is not explicitly junior.

**Relevant responsibilities:** Draft, review, redline and negotiate commercial agreements; help build tools and workflows that improve turnaround time, reduce cycle times and legal exposure, and create consistency in review processes through checklists; and maintain contract records, track key provisions and monitor renewal deadlines.

**Connection to this PRD:** Supports checklist-based review, consistent handling across contracts and renewal tracking. It states goals for turnaround and consistency, not a measured problem.

**Source limitation:** The posting was removed on October 20, 2026\. The responsibilities come from the Built In copy of the posting read on November 4, 2026, and the link may no longer show the full text.

[Posting copy — LegalShield (PPLSI)](https://www.builtinboston.com/job/paralegal/11303138)

**Pylon**

**Role:** Legal & Contract Ops, listed in San Francisco. This is an in-house role at a startup and is not explicitly junior.

**Relevant responsibilities:** Own contract review and help build the contract operations process from scratch as the company scales from 10M to 100M ARR. The posting states: “We have a contract bottleneck problem,” “Every redline that sits too long kills a deal,” and “We're doing 10+ customer contract reviews per month and growing fast.”

**Connection to this PRD:** This is the only posting found that states the problem directly: slow contract review is a bottleneck that costs deals. Its fit is limited. The volume is 10 or more reviews a month, far below a 30-contract diligence batch. The review is of customer contracts and redlines, not clause extraction for diligence. No clause types are named.

**Source limitation:** The wording is the same in two aggregator copies (JoinRise and Sonara). JoinRise lists the role as open and posted December 17, 2025; Sonara shows no date. Its status was not confirmed on Pylon’s own site.

[Posting copy — Pylon (JoinRise)](https://joinrise.co/pylon/legal-contract-ops-i9id)

### **How this evidence informs the PRD**

**Primary user:** Retain junior corporate associates and corporate contracts paralegals. Andrews Myers anchors Maya’s junior role; ImmunityBio supplies the clearest clause-level connection.

**Trigger:** A reviewer receives agreements and a due diligence checklist for a transaction. The postings support the transaction and diligence context; the specific 9 a.m. scenario and 30-contract batch remain illustrative.

**Workflow:** Upload contracts, choose clause categories, verify extracted passages and export a review table. This is a proposed product workflow, not a process documented verbatim in the job descriptions.

**Checklist:** Assignment and change of control have direct support in the ImmunityBio and Cantor Fitzgerald postings. Renewal, governing law and termination for convenience remain proposed categories to validate with reviewers and map to CUAD labels.

**Human review:** Retain the separation between extraction and legal interpretation. Source highlights and reviewer corrections support checking the evidence before senior lawyers determine its significance.

### **Questions for practitioner validation**

1. In your last diligence review, how many contracts did you check and which clause categories did you record?  
2. Which takes the most time: finding passages, interpreting them, copying them into a table, or resolving questions?  
3. What tools do you already use, and where do they leave manual work?  
4. Would a table of exact quotations and their locations save time after you verify its results?  
5. What should happen when no relevant passage is found, and which omissions would be most consequential?

**Evidence boundary:** The existing pain-point statements and time-saving targets remain hypotheses and proposed targets. These JDs strengthen the link to real responsibilities without demonstrating those outcomes. E-Space and LegalShield state goals and duties, not complaints, and both are in-house roles. Pylon states a contract bottleneck directly, but for customer contract redlines at a startup, not diligence review. Cantor Fitzgerald supports the duties and states no pain.

# **EVALUATION PLAN**

This tab holds the measurements that follow the build window (November 5 to 7, 2026). The evaluation targets, the reviewer pilot and the answer-key checks sit here, apart from the build requirements in section 3, so that the P0 scope can be built and demonstrated first. Owner: Kerrian Gordon and Mara Munoz.

## Schedule

* **November 5:** written definitions of the five categories due (Kerrian Gordon).  
* **November 6:** Mara Munoz records her marks on 10 test contracts.  
* **End of November 7:** the answer key, the written definitions and the extractor prompts are frozen and tagged. No test-split contract is used for development before then.  
* **November 8:** buffer for the CUAD loader, the evaluation script and the pilot setup.  
* **November 9 to 11:** first run on the test split, scoring and the reviewer pilot.  
* **November 12:** project deadline.

## Targets

* **Give reviewers a first-pass table in minutes.** Metric: minutes per contract and clauses missed per contract, in a counterbalanced pilot with at least 2 reviewers. Each reviewer does some contracts with the tool and some by hand, and every contract is reviewed both ways. Time includes checking the tool's output. Missed clauses are counted against the answer key, the CUAD-labelled clauses in each test contract, fixed before testing and owned by Kerrian Gordon. Target: median per-contract time at least 30% lower with the tool, and lower on most paired contracts, with no more missed clauses than manual review. Reported as a pilot, with the per-contract range.  
* **Find the checklist clauses reliably.** Metric: recall per category on the 102 held-out contracts in CUAD's test split, counting a match when predicted and labeled spans overlap by at least 50%. Target: average recall of 0.80 or higher across the 5 categories.  
* **Keep false matches low.** Metric: precision and F1 per category after verification on the same CUAD contracts, compared with a regex-only baseline (the regex pass of the extractor with no model), reported with the raw counts of matches, false matches and misses. Target: average precision of 0.70 or higher across the 5 categories, and average F1 at least 10 points above the baseline's average.  
* **Keep processing time practical.** Metric: minutes from upload to all findings for the 30 largest contracts in CUAD's test split (up to about 100 pages) against 5 categories, on a run with an empty cache. Target: 30 minutes or less.

The two guarantees that hold by construction, 100% verbatim quotations and 100% visible gaps, stay in the success metrics in section 2d, because they can be demonstrated in the build window.

## Answer key and definitions

**Decision:** Usability-test contracts and the answer key come from CUAD. The key is the list of CUAD-labelled clauses in each test contract, fixed before testing so that missed clauses can be counted. The test contracts are drawn from the held-out set, so the extractor is not tuned on them. Owner: Kerrian Gordon. Decided November 4, 2026\.  
**Decision:** Mara Munoz independently marks 10 of the test contracts, without seeing the CUAD labels, to check them before the test. Kerrian Gordon draws the 10 with a recorded random seed, so that at least 3 of them contain each of the five labels. This is a spot check of the key, not an estimate of its error rate; the evaluation reports the number of disagreements. Mara starts marking only after Kerrian has signed the written definitions. Mara records her marks by November 6, 2026, in a separate sheet that holds no CUAD labels ([Clause key check: Mara's marks](https://docs.google.com/spreadsheets/d/1kmxT5aGjQXIzzYN5r4xWlO6X0UIIL3jjHxpvnU1VZ88/edit)). Decided November 4, 2026\.  
**Decision:** Each of the five categories has a short written definition, based on the category descriptions published with CUAD, saying what counts as a clause. Mara marks against these definitions and the extractor is scored against them. Owner: Kerrian Gordon. Due November 5, 2026\. Decided November 4, 2026\.  
**Decision:** The answer key, the written definitions and the extractor prompts are frozen at the end of November 7, 2026, and the frozen version is tagged. No test-split contract is used for development before then, and the first run on the test split is on or after November 9, 2026\. Owner: Kerrian Gordon. Decided November 4, 2026\. Revised November 5, 2026: the freeze moved from the end of November 6 to the end of November 7 to match the build window.  
**Decision:** Where Mara's marks differ from a CUAD label, both are recorded and Kerrian and Mara review the contract together against the written definition. The outcome is one of three: the CUAD label stands, the label is corrected, or the item is dropped as ambiguous. Each change is logged with its reason in the disagreement log ([Clause key check: Disagreement log](https://docs.google.com/spreadsheets/d/14NnC7_-4Chilgv-5_QtE7OhM-sEf6YrAmoV_u4LzUpI/edit)), a sheet that Kerrian maintains, and made before the freeze. The evaluation reports how many were changed. Items dropped as ambiguous are removed from scoring and reported as a count. At the freeze the log is exported to a CSV and stored with the tagged version. Owner: Kerrian Gordon and Mara Munoz. Decided November 4, 2026\.  
**Decision:** The final evaluation uses Claude Sonnet through the facilitator's API key, with a spending limit of \$40. Owner: Kerrian Gordon and Mara Munoz. Decided November 4, 2026\.  
**Decision:** The five checklist categories map to these CUAD labels, as spelled in the data files: assignment is Anti-Assignment, change of control is Change Of Control, termination for convenience is Termination For Convenience, renewal is Renewal Term, and governing law is Governing Law. Checked against the CUAD data files on November 4, 2026\. Governing Law spans are clause sentences (median 28 words), so the 50% overlap rule applies. Anti-Assignment and Change Of Control spans overlap in some contracts, so each category is scored on its own. Notice Period To Terminate Renewal and Expiration Date are not mapped. The held-out set is CUAD's test split of 102 contracts, and evaluation uses all of them. Development uses the other 408 contracts. In the test split, 26 contracts have a Change Of Control label and 26 have Renewal Term, so recall for those two categories is noisy. Decided November 4, 2026\.  
**Decision:** Notice of non-renewal is out of scope. Renewal is scored against CUAD's Renewal Term label only, the written definition of Renewal excludes notice periods, and the extractor's Renewal description is changed to match. Notice Period To Terminate Renewal is not mapped or scored. Owner: Kerrian Gordon. Decided November 4, 2026\.