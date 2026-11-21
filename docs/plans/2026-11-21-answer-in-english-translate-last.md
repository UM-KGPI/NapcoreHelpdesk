# Plan: answer and check in English, translate last

Written 2026-11-21 against 0.97.242. Each claim is labelled **measured**, **believed** or **assumed**.

## 1. What is wrong today

The sources are in English. For a question in another language the model writes the answer in that language,
and the answer check (`_validate_generated_answer`, `backend/helpdesk/services/llm_generator.py`) then compares
its words with the words of the English passages. At the first sentence that fails, the whole draft is thrown
away and written again. If the second draft fails too, it is served anyway, marked as not validated, with
confidence capped at 0.80 (**measured**: read in the code).

From a capture of 40 questions asked twice on dev (the check's inputs stored; a replay reproduces all 104
stored verdicts, **measured**):

| | Not English | English |
|---|---|---|
| First drafts rejected | 15 of 18 runs | 12 of 60 runs |
| Served as not validated after two failures | 12 | 2 |
| Median time when rejected | 13.0 s | 6.5 s |

Of the 64 rejected sentences, the cited passage supports 55 (read one by one; up to 4 are borderline). 46 of
the 55 are answers not in English. One such question took 6 model calls and 17.2 s: the language was named
twice, the answer was written twice, and both rejected sentences were right.

## 2. The solution

Everything up to and including the check works in English, the language of the sources. Translation into the
language of the question is the last step.

| # | Step | Model call | Today |
|---|---|---|---|
| 1 | Language of the question and its English form | one call, only when the question is not clearly English | up to three calls (language named twice, translation) |
| 2 | Scope check, on the English form | one | one |
| 3 | Retrieval, on the English form | none | none |
| 4 | Draft, in English | one | one, in the question's language |
| 5 | Check, in English. Every sentence gets a verdict; a failed sentence is removed, the rest is kept | none | whole draft rejected at the first failure, then a second draft with thinking |
| 6 | Only for a question not in English: the checked answer is rendered into the question's language | one | none |

For a question in English steps 1 and 6 do not run: one call less than today whenever the draft would have been
rejected, otherwise the same. For a question in another language: four calls, where today it is five or six.

Rules of step 5:

- The check does not stop at the first failure. The same draft always gives the same result.
- A sentence is not cut inside a parenthesis.
- The model is asked again only when what remains no longer answers the question, once, with the removed
  sentences as feedback. Text that failed the check is never served as if it had passed.

Rules of step 6:

- The rendering keeps every citation mark, identifier, code span, number and quoted text of the checked answer.
  This is verified by comparing the two texts, without a model. If it fails, the rendering is made once more;
  if it fails again the English answer is served with a note.
- The rendering is sent to the user as it is written, so the wait before the first words does not grow by the
  whole step.

## 3. Steps and gates

The gates are fixed here, before any run. A step that fails its gate is reverted and recorded.

### Step 1: English up to the check, translation last (steps 1 to 4 and 6 of the table)

Measured on a new capture: the 9 non-English questions of the first capture and at least 10 more, twice each,
and the English questions as control. About 200 model calls.

| | Must hold | Today |
|---|---|---|
| First drafts rejected, not English | at most 30 % | 15 of 18 |
| Served as not validated, not English | at most 2 of 38 runs | 12 of 18 |
| Model calls per non-English answer, median | at most 4 | 6 |
| Median answer time, not English | at most 10 s | 13.0 s when rejected |
| Rendering in the question's language | every run | |
| Citation marks, identifiers, code, numbers kept in the rendering | every run | |
| Claims in the rendering that the checked answer lacks, read one by one | none | |
| English questions | the replay of their stored calls is identical | |
| Retrieval and example benchmarks | unchanged | |

### Step 2: a verdict per sentence, removal instead of rewriting (step 5 of the table)

Before it, every cited sentence of the captured first drafts is labelled supported or not by reading it against
its passages, the accepted ones too. Measured by replay on the stored drafts, then a capture of the 40 questions
twice to read what is served (about 190 model calls).

| | Must hold | Today |
|---|---|---|
| Runs with a second draft | at most 10 % | 27 of 79 |
| Answers served with text that failed the check | none | 14 of 78 |
| Supported sentences removed | at most 10 % | not applicable |
| Unsupported sentences that today's check rejects | all still removed | 9 of 9 |
| Served answers, read one by one | each answers the question or says plainly what is missing | |
| Questions where the two runs differ on a second draft | at most 4 of 40 | 11 of 40 |

One decision is mine before this step: what the user sees when too little remains after one rewrite. My choice
unless the reading says otherwise: the supported sentences with a visible note that part of the answer could not
be confirmed in the sources, and a refusal when no sentence is supported.

### Step 3: prod

After each shipped step: the questions that were rejected on prod asked again, two or three times each, and the
share of answers with a second draft and with unconfirmed text read from the log for a week.

## 4. Not in this plan

- New rules for single languages, standards or kinds of document.
- Replacing the word comparison by closeness of meaning (the embedding model). With the check always in English
  it is not needed for the main cause. It comes back only if step 2 misses its line on supported sentences.
- The error when a retrieval event is saved without a commit id, seen once in the capture. A separate fix.

## 5. Risks

- **The rendering can change a claim.** The names, numbers and citations are compared without a model; the
  wording is read in the step 1 gate, on a sample. This is the main new risk.
- **English drafts still fail the check sometimes** (12 of 60), mostly for facts with no name in them. Step 2
  turns such a failure from a rewritten answer into one removed sentence; it does not make the check right.
- **Naming the language with one call.** Today a separate, stronger model names the language of short questions,
  kept on purpose after wrong guesses between close languages. Step 1 measures the language of every rendering,
  and that line must hold in every run; if it does not, the separate naming stays, once per question.
- **The yardstick is small**: 40 questions, one reader for most labels.
- **Believed, not checked:** that English drafts for non-English questions are rejected as rarely as drafts for
  English questions. That prod behaves as dev does here.
