---
name: create-pr-description
description: Generate a well-structured pull request description based on the actual diff between the current branch and `main`, then save it to a file the user can copy directly into GitHub.
---

## Open source PR best practices

Apply these principles when drafting the description. List them here so the skill can reference them consistently:

1. **Context over code** — explain *why* the change was needed, not just what files changed. Reviewers should understand the problem before reading any diff.
2. **One logical change per PR** — the description should reflect a focused scope. If the diff spans unrelated concerns, note that in the intro so the reviewer knows it is intentional.
3. **Friendly, humble intro for first-time contributors** — acknowledge that this is a contribution to someone else's project. A short sentence expressing gratitude or context (e.g. "I ran into this while following the quickstart") builds trust with maintainers.
4. **Explicit testing evidence** — describe what you ran to verify the change, even if it is manual. Open source maintainers cannot run every PR locally before reviewing.
5. **Respect the project's commit and style conventions** — note the convention used and flag if you are unsure. Maintainers should not have to guess whether you checked.
6. **No trailing todos or apologies** — do not leave placeholder text or apologies ("sorry if this is wrong") in the final description. State what was done confidently; invite feedback in a question.
7. **Link related issues or prior PRs** — if the change follows up on a previous issue or PR, reference it explicitly using `#number` so GitHub auto-links it.
8. **Keep sections scannable** — use headings for logical groups, short paragraphs, and no long bullet lists. Reviewers skim before they read.

---

## Steps

### 1. Detect current branch

Run:
```bash
git branch --show-current
```

If the current branch is `main`:
- Tell the user: "It looks like you are on the main branch. I will create a draft PR description based on your modified files instead of a branch diff."
- Skip to the **Modified files on main** flow below.

---

### 2. Standard flow: branch vs main

Get all commits on the current branch that are not on main:
```bash
git log main..HEAD --format="%H %s"
```

Get the full diff of all changes:
```bash
git diff main..HEAD
```

Get only the list of changed files and whether they are modified (M), added (A), deleted (D), or renamed (R):
```bash
git diff main..HEAD --name-status
```

---

### 3. Modified files on main flow

If on main, get the current uncommitted changes instead:
```bash
git diff --name-status
git diff
```

---

### 4. Identify new files and ask the user

From the `--name-status` output, separate files by status:
- **Modified (M):** always include in the analysis
- **Deleted (D):** always include in the analysis
- **Renamed (R):** always include in the analysis
- **Added (A):** do NOT include by default

If there are any added (A) files, ask the user before including them:

> "I found the following new files in the diff. Would you like to include them in the PR description? Most of the time these are local test files, so I am skipping them by default.
>
> - `path/to/new_file.py`
> - `path/to/another_file.md`"

Wait for the user's answer before proceeding.

---

### 5. Detect commit convention

Look at the commit subjects from step 2 (or recent git log if on main) to detect whether the project uses Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:` etc.). Also check if commits use scopes like `docs(readme):`.

Use the detected convention to suggest the PR title. If no convention is detected, use a plain descriptive title.

---

### 6. Draft the PR description

Using the diff, commit history, and the open source best practices listed above, produce a PR description with the following structure:

```
# <type(scope): short description of the PR>

<2-4 sentence intro. If this is a first-time contribution or follows up on a previous issue or PR,
say so here. Explain what motivated the change from the contributor's perspective.>

---

## What changed and why

### <Group 1: logical area of change>

<Explanation of what changed and the reason behind it. Focus on the why, not just the what.>

### <Group 2: another logical area>

<Explanation.>

... (one section per logical group of changes)

---

## Testing

<Describe how the change was verified. Include commands run, output observed, or steps taken manually.
If no automated tests cover this change, say so and describe the manual check instead.>

---

## Notes for reviewers

<Optional. Flag anything the reviewer should pay special attention to, open questions you have,
or conventions you followed (or deviated from) and why. Omit this section if there is nothing to flag.>
```

Guidelines for the description body:
- Write for GitHub's markdown renderer: do NOT hard-wrap lines. Each paragraph or bullet should be a single long line so GitHub renders it correctly without spurious line breaks.
- Use bullet points freely to list changes, steps, or items — they render well in GitHub and help reviewers scan quickly.
- Group changes by logical area, not by file.
- Lead each section with the problem that motivated the change, then the fix.
- Use plain language and short sentences.
- Do not list file names unless they are directly relevant to understanding the change.
- Keep the intro short — 2-4 sentences max.
- Apply all eight open source best practices from the top of this skill.

---

### 7. Save the description to a file

After drafting the description, save it to a file at the repo root:

```
pr-description.md
```

Tell the user:
> "I saved the description to `pr-description.md` at the repo root. You can open it, copy the contents, and paste directly into GitHub's PR body field."

Do NOT commit this file. It is a local working file for the user.

If `pr-description.md` already exists, overwrite it without asking — it is always regenerated, never a source of truth.

---

### 8. Present and offer refinements

Show the draft inline in the chat as well (do not make the user open the file to see it), then ask:
- "Does this capture everything? Let me know if you want to adjust the tone, add more detail to any section, or change the title. Once you are happy with it, `pr-description.md` is ready to paste into GitHub."
