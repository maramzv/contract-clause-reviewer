# Before you share the repo

A short checklist for Kerrian and Mara, and for any later project. Each item comes from something we nearly missed on Clautra.

## 1. Open it as a stranger would (the one habit)

Open the repo in a private window, on the **default branch** (here `main`), and read the front page cold.

- Does it open with the problem, in plain words, before the tool?
- Do the images load and do the links work? Use relative paths such as `docs/images/clautra-overview.jpg`, not branch-tied URLs.
- Is anything stale: an old name, a "not built yet" list that is no longer true, a folder that contradicts the deck?

We only learned that `main` was still on the first commit when we asked which branch GitHub shows. Merging to `developer` is not publishing.

## 2. Say what is not proven

- Next to each claim, say whether it was measured. Time saved was never tested, so the README, deck and post say so.
- Keep results and limits together. Recall and precision missed their targets, and the README says so.

## 3. Check what goes out

- No `.env`, databases, answer keys, or API-key text in the tree. Search it before opening a `developer` to `main` pull request.
- Large files: GitHub blocks files over 100 MB, and uploads in the README editor are limited to 10 MB on a free plan.
- Public contracts only.

## 4. Keep the pieces in step

- The README, the PRD and the deck should agree on the name, the features and the numbers. Change one, check the others.
- Remove old copies of the deck and notes instead of keeping two that disagree.
- State the demo video's real length next to its link.

## 5. Make the history readable

- Commit messages say what changed, not "fix" or "update".
- Use a merge commit for `developer` into `main`, so the history stays visible.
- Name the product the same way in the README title, the app and the docs, and note an old name once.
