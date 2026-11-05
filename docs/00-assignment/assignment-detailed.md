# Building for a JD

**Goal:** Learn to separate what a job description (JD) says outright from what it is actually revealing.

**Objectives**

1. **Distinguish** between explicit duties and implied realities in a JD.
2. **Identify** language that signals repetitive, manual work worth building for.
3. **Practice** reading a JD's two layers using the lesson's method.

## Lesson: "Reading a JD"

### Part 1: Two Layers of a JD

Plain terms: **what it says, what it reveals.** Every job description has two layers. One is written down. The other shows what the work is really like.

1. **Explicit:** the duties, tools and qualifications the JD lists outright.
2. **Implied:** the daily reality behind those duties, which the JD never says directly.
3. **Why it matters:** the implied layer shows where a person's time really goes.

**Example**

- **What the JD says:** "Coordinate schedules across teams"
- **What it reveals:** Someone spends hours each week chasing people for their availability.

### Part 2: Read Between the Lines

Plain terms: **three passes over one JD.** Read the JD twice: first for what it says, then for what it quietly tells you about the work.

1. **Underline** the explicit duties, one line each.
2. **Ask:** what must be true for this duty to exist? What is that person's day like?
3. **Write** one implied reality next to each duty, in plain words.

**Examples**

- **Says:** "Maintain tracking spreadsheets" → **Reveals:** manual data entry, copy and paste
- **Says:** "Respond to customer inquiries" → **Reveals:** the same questions, over and over
- **Says:** "Compile weekly status reports" → **Reveals:** hours collecting numbers from many places

### Part 3: Signals of Repetitive Work

Plain terms: **words that point to manual tasks.** Some words in a JD point to work done by hand, again and again. Those are good places to look for a build.

1. **Frequency:** daily, weekly, each, every, high volume, or on a recurring basis.
2. **Actions:** track, update, compile, reconcile, schedule, respond, enter, maintain.
3. **Handoffs:** coordinate with, partner with, or follow up with other people.

**Word lists**

- **How often:** daily, weekly, each, every, high volume, recurring
- **What they do:** track, update, compile, reconcile, schedule, respond, enter, maintain
- **Who they chase:** coordinate with, follow up with, partner with

### Part 4: Is It Worth Building For?

Plain terms: **four checks before you choose.** Not every JD is a good Cycle 4 candidate. Check each one before you add it to your shortlist.

1. **Specific:** it names a real role and real tasks, not vague goals.
2. **Research-able:** you can find or talk to someone who does this job.
3. **Buildable:** the work repeats and has several steps that agents could split up.

In practice this is four checks, because "Buildable" splits in two:

- **Specific:** a real role, with real tasks
- **Research-able:** you can ask someone who does it
- **Repetitive:** happens often, mostly by hand
- **Multi-step:** more than one agent's worth

## The process

1. Learn the two-layer method (Parts 1–2).
2. Look for the repetitive-work words (Part 3).
3. Add a JD to your shortlist only after it passes all four checks (Part 4).

## How this applies to our build

### What we are building

Contract Clause Extraction and Review is a web app that helps legal reviewers go through a batch of commercial contracts. The reviewer uploads the contracts and picks which clause types to look for (assignment, change of control, termination for convenience, renewal, governing law). The app pulls out the matching wording, shows the exact quote and its page, and flags anything it could not find so a person checks it. The reviewer accepts or removes each result and exports a table.

The target users are junior corporate associates and contracts paralegals. They do this kind of review during deals and due diligence.

### Two layers: says vs. reveals

We started from real job postings for these roles.

- **What the postings say:** review contracts for assignment and change-of-control provisions, track renewal deadlines, escalate non-standard terms, and conduct due diligence.
- **What that reveals:** the same clause types get searched for in every agreement, and the findings have to be copied into a table by hand. It also means a reviewer can't tell whether a clause is missing or just wasn't found.

The reading of what the postings reveal is our hypothesis, not something the postings state.

### Repetitive-work signals

The postings use the kind of language that points to manual, repeated work:

- **How often:** each contract, every agreement, high volume
- **What they do:** track, review, monitor, escalate
- **Who they chase:** coordinate with legal and finance, escalate to a senior lawyer

### The four checks

- **Specific:** Yes. It is a named role (junior associate or contracts paralegal) with a defined task: finding set clause types across a batch of contracts.
- **Research-able:** Partly. Real postings and a public labeled dataset (CUAD) exist.
- **Repetitive:** Probably. Reviewers apply the same clause checklist to every contract in a batch, and the job postings describe this kind of repeated review work.
- **Multi-step:** Yes. The work has several connected steps: read the files, split them up, find candidate passages, verify each quote against the contract, store the results, let the reviewer check them, and export.

