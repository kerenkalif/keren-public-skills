---
name: kerenkalif-moodle-quiz-from-slides
description: Turns lecture slides (any subject, any lecturer) into a question bank, a validated Moodle XML file with one category per presentation, and optionally a quiz with a random question per category. Hebrew/RTL and English/LTR. הופך מצגות הרצאה למאגר שאלות ולקובץ Moodle XML. Use when asked for a quiz or exam questions for Moodle from presentations.
---

# Slides → question bank → Moodle

Guides a lecturer from presentation files to questions in the Moodle question bank, one category per presentation. Works for any subject. Reply in the lecturer's language.

**Principle:** the lecturer owns the content, so there are two mandatory stops (step 2: approve the bank; step 4: import into Moodle by hand). Between them, work without unnecessary questions and report only errors.

## Step 0: opening questions (once, all together)
Ask in one message (use AskUserQuestion if available). Do not re-ask what was already said:
1. Which presentations to include; are the files attached? If not, ask to attach them.
2. How many questions per presentation (default 6–9) and which types: multiple choice, matching, gap fill (select from a list).
3. Main category name in Moodle (usually the course name) and an ID prefix for question IDs (e.g. `CS101-`).
4. Numbering of question IDs. Default: `<presentation number>.<question number>` (e.g. `3.01`). If the lecturer already has banks in the same course, ask for the last number used and continue after it, so IDs never collide.
5. Language and direction: right-to-left (Hebrew, Arabic) or left-to-right. Wording of the questions (e.g. addressing students in plural) and which terms stay in English.
6. How many questions each student gets in the quiz (one random question per presentation, or more), and whether the number from each presentation should be uniform across students.

## Step 1: read the slides and write the bank
- Read each presentation fully, including speaker notes. Extract the main topics, definitions and examples.
- Every question relies on what the slides teach: no outside knowledge, and no questions whose answer is obvious from the wording.
- Multiple choice: four options, plausible distractors based on real misunderstandings. Spread the correct letter across A–D (no letter above 40%). The explanation says why the answer is right.
- Matching: 3–6 term/definition pairs, each unambiguous.
- Gap fill: a sentence with exactly one `___` and a list of options. The answer is the exact text of one option.
- Each question states its source: presentation code and slide number. If unsure of the slide number, mark that explicitly; never guess.
- Check calculation questions by actually computing them.

### Format (`bank.txt`)
Write the bank as a plain text file in this format. It is the source of truth for the build:

```
## Lecture 03 – Sorting
# 3.01 | Multiple choice | 03, slide 4
Q: Question text
Q: A. First option
Q: B. Second option
Q: C. Third option
Q: D. Fourth option
A: B. Short explanation of why.
# 3.02 | Matching | 03, slides 5-6
Q: Match each term:
Q: Term one
Q: Term two
A: Term one ← its explanation
A: Term two ← its explanation
# 3.03 | Gap fill (select from list) | 03, slide 7
Q: A sentence with ___ in place of the missing word.
Q: Options:
Q: Option 1
Q: Option 2
A: Option 1
```

- `##` starts a presentation; its text becomes the Moodle category name.
- The type may be written in English (`Multiple choice`, `Matching`, `Gap fill (select from list)`) or in Hebrew (`אמריקאית`, `התאמה`, `השלמה (בחירה מרשימה)`). Letters may be A–D or א–ד. For Hebrew use `Options:` as `אפשרויות לבחירה:`.
- In matching, each `A:` line is `term ← explanation`, in the same order as the terms.

## Step 2: stop 1 — bank approval
Present the bank to the lecturer and ask them to review, delete, fix and approve. **Do not continue without explicit approval.**

- If a document tool is available (Docs artifact or similar), create an editable document from `bank.txt` and show the link. Structure: a level-2 heading per presentation, then one table with header `No. | Type | Source | Question | Answer and explanation` (Hebrew: `מס' | סוג | מקור | שאלה | תשובה והסבר`), one row per question, one paragraph per line in the question and answer cells, and a short summary section at the end (counts per presentation and type).
- Without a document tool, send `bank.txt` as a file.
- Tell the lecturer to write back when they finish editing and approve (e.g. "When you finish editing and approve, write me here, and I will read the updated document and continue to the conversion"). End the turn and wait. If they write that they finished while the document is still being filled, say so, finish filling, and ask again.
- Mention what to check: slide numbers, spread of correct answers, and questions based on spoken remarks that are not on the slides.
- After they edit, read the updated document (not the old version from memory) and apply their changes to `bank.txt`.

## Step 3: convert to Moodle XML and verify
The scripts are in this skill's `scripts/` folder (copy them to the working directory).

```
python3 scripts/txt2doc.py bank.txt doc.xml            # add --en for English table headers
python3 scripts/build.py doc.xml moodle_quiz.xml "<main category>" "<id prefix>"   # add --ltr for left-to-right languages
```

`build.py` prints `questions N categories M errors [...]`. Verify:
- No errors, and N equals the number of questions in `bank.txt`.
- Every multiple-choice question has exactly one `fraction="100"`.
- In gap-fill questions `[[k]]` points to the correct option and k is within the number of options.
- All question IDs are unique.
- Counts per category and type. Report them to the lecturer in short.

The question name and ID are `number | presentation code | first 45 characters`.

## Step 4: stop 2 — import into Moodle (manual)
The browser cannot upload files automatically, so the lecturer uploads the file. Send the file and explain:
1. Course → Question bank → in the dropdown choose **Import**.
2. Format **Moodle XML**; under General make sure **"Get category from file"** is ticked.
3. Choose the file, upload, and click **Import**. The number of questions should match step 3.
4. **Import once only.** Importing again into the same categories creates duplicates. To fix a question, edit it in Moodle or delete the category first.
5. Moodle may warn about a matching question with fewer than three distinct answers. It is fine to continue.

Wait for the lecturer to confirm the import worked, then offer step 5.

## Step 5: build the quiz (optional)
Explain, or do it together if a browser with a signed-in user is available:
- Create a new quiz (it can be hidden until the date).
- For each presentation add a **random question** from that presentation's category, so each student gets a different variation. If the quiz should have N questions, split them evenly across presentations (give the extra ones to the largest banks) so every student gets the same number from each part.
- Set answer shuffling, attempts and time limit as the lecturer decides.
- Final check: open a preview and verify that text direction and English terms display correctly.

## Pitfalls
- Category and question names are wrapped in BiDi isolation marks (RLI/PDI) in right-to-left mode. This is deliberate; do not strip them. With `--ltr` they are not added.
- If `errors` is not empty, fix the format of the problematic question in `bank.txt` and run again. Do not work around it.
- English terms inside Hebrew text are wrapped automatically. If something looks reversed in Moodle, check the source text before changing the script.
- Question IDs must be unique across the whole course question bank; keep the numbering from step 0.

## License
MIT. See `LICENSE`.
