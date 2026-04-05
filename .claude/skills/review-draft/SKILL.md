---
name: review-draft
description: Review a writing draft or .md document for typos, grammar, word choice, sentence flow, structure, and formatting. Applies corrections directly to the file and generates a feedback_for_future.md table the user can save to personal notes.
---

## Purpose

This skill reviews a written draft or Markdown document and does two things:

1. **Applies corrections** directly to the source file so it is ready to publish or share.
2. **Generates `feedback_for_future.md`** — a structured file with categorized tables of every issue found, so the user can study the patterns and improve their English writing over time.

The goal is not just to fix the current document, but to help the user build better writing habits.

---

## Guiding principles

- **Preserve the author's voice.** Correct errors without rewriting personality out of the text. If the user has a casual, conversational tone, keep it.
- **Explain, don't just fix.** Every correction must have a reason — this is a learning tool, not just a cleanup tool.
- **Be specific in the tables.** Vague feedback like "awkward sentence" is not useful. State clearly what the problem was and what the rule is.
- **Be encouraging.** The user is actively working on their English. Frame feedback positively and constructively.

---

## Steps

### 1. Identify the file to review

If the user provided a file path in their message, use it directly.

If no file was specified, ask:

> "Which file would you like me to review? Please provide the file path (e.g. `posts/post1.md`)."

Wait for the user's answer before proceeding.

---

### 2. Read the file

Read the full content of the file. Do not start reviewing until you have read the entire document.

---

### 3. Perform the full review

Analyze the document across all four categories below. Collect every issue before making any edits — do not fix issues one at a time.

#### Category A — Typos
Misspelled words, accidental double words, wrong capitalization of proper nouns or the pronoun "I".

Examples of what to catch:
- `appication` → `application`
- `dillema` → `dilemma`
- `begging` → `beginning` (when the meaning is "the start of something")
- `i have` → `I have` (the pronoun "I" is always capitalized in English)
- `persdonal` → `personal`

#### Category B — Grammar Issues
Problems with sentence structure, tense, punctuation, or agreement.

Examples of what to catch:
- **Comma splices:** Two independent clauses joined with only a comma. Fix by using a period, semicolon, or a coordinating conjunction.
  - Wrong: `It was interesting, However, I have a dilemma.`
  - Right: `It was interesting. However, I have a dilemma.`
- **Wrong verb tense:** `if I ever left the company` → `if I ever leave the company` (conditional requires present tense)
- **Run-on sentences:** Very long sentences with many ideas chained together. Split them.
- **Missing articles:** `I have vault` → `I have a vault`
- **Subject-verb agreement issues**

#### Category C — Word Choices
Words that are technically understandable but imprecise, informal in the wrong context, or replaced by a more accurate term.

Examples of what to catch:
- `generic notes like "do 1hr of workout"` → `recurring reminders like...` ("generic" implies unimportant; "recurring" is accurate)
- `checkout the goals` → `review the goals` ("check out" is casual and vague; "review" is intentional)
- `thinks` → `things` (if contextually wrong, not just a typo)

#### Category D — General (Flow, Structure, Formatting, and Other)
Everything that is not a typo, grammar error, or word choice issue:

- Sentences that are too long and hard to follow
- Paragraphs that cover too many ideas at once (suggest splitting)
- Repeated information across paragraphs (flag it and consolidate)
- Formatting improvements (e.g., bolding a video title, using a colon to introduce a question)
- Structural suggestions (e.g., moving a clarifying paragraph to a better position)
- Tone consistency

---

### 4. Apply all corrections to the source file

Rewrite the file with all corrections from categories A, B, C, and D applied.

Rules for rewriting:
- Keep the original paragraph structure unless a structural change is explicitly needed.
- Keep the author's tone — do not make the text sound more formal than the original unless that was the issue.
- Do not add content that was not in the original.
- Do not remove content unless it is a duplicate of something already said.

After saving the file, confirm to the user:

> "I've applied all corrections to `<filename>`. See below for the full feedback breakdown."

---

### 5. Generate `feedback_for_future.md`

Create (or overwrite) a file called `feedback_for_future.md` in the same directory as the reviewed file.

The file must contain four tables, one per category. Use this exact structure:

```markdown
# Writing Feedback — <filename> (<date>)

> Use this file as a personal reference. Study the patterns across sessions to build better writing habits.

---

## Typos

| # | Original (wrong) | Corrected | Rule / Note |
|---|-----------------|-----------|-------------|
| 1 | `wrong word` | `correct word` | Brief explanation of why this is a typo and how to avoid it |

---

## Grammar Issues

| # | Original (wrong) | Corrected | Rule / Note |
|---|-----------------|-----------|-------------|
| 1 | `wrong sentence or phrase` | `corrected version` | Name the grammar rule and explain it simply |

---

## Word Choices

| # | Original | Better Choice | Why |
|---|----------|---------------|-----|
| 1 | `original word or phrase` | `better alternative` | Why the replacement is more precise or appropriate |

---

## General (Flow, Structure & Formatting)

| # | Category | Issue Found | Recommendation |
|---|----------|-------------|----------------|
| 1 | Flow / Structure / Formatting / Other | Description of the issue | What was done to fix it and why |
```

Rules for the tables:
- Every single issue found in step 3 must appear in the appropriate table — do not skip minor ones.
- The **Rule / Note** and **Why** columns must be written in plain, friendly English — explain as if teaching a non-native English speaker.
- Use backticks around original and corrected text inside table cells for readability.
- Number rows starting from 1 in each table.
- If a category had zero issues, still include the table but add a single row: `| — | No issues found | — | — |`

After saving the file, tell the user:

> "I also saved `feedback_for_future.md` next to your file. You can copy those tables into your personal notes to track your writing patterns over time."

---

### 6. Show a brief inline summary

After both files are saved, display a short summary in the chat — not the full tables, just the counts:

> **Review complete for `<filename>`**
>
> | Category | Issues found |
> |----------|-------------|
> | Typos | N |
> | Grammar Issues | N |
> | Word Choices | N |
> | General | N |
>
> Full details are in `feedback_for_future.md`. Let me know if you'd like to discuss any of the changes or adjust the tone of the rewrite.

---

### 7. Offer follow-up

End with a short, open invitation:

> "Would you like me to walk through any specific change, or is there anything about the rewrite you'd like adjusted?"
