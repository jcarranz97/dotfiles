---
name: create-pr-description-pycro
description: Generate a well-structured pull request description for the pycro project, following linkfy's commit conventions and contributor tone. Saves the result to pr-description.md at the repo root.
---

## Pycro project conventions

Keep these in mind throughout — they shape both the title and the body:

1. **Conventional Commits with scopes** — commit subjects follow `<type>(<scope>): <subject>`. Allowed types: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`, `merge`. Scopes seen in the history: `runtime`, `input`, `build`, `ci`, `ios`, `android`, `web`, `governance`, `release`, `incidents`, `readme`. Use the scope that matches where the change lives.
2. **Early-stage, solo-maintained project** — linkfy is the sole maintainer and actively reviews first-time contributions. Tone should be warm, humble, and respectful of their time.
3. **No CONTRIBUTING.md yet** — acknowledge that you checked the commit history and `docs/branch-commit-workflow.md` to follow conventions. Mention this in the notes section so the maintainer knows you did the homework.
4. **Branch naming observed in history** — maintainer uses `codex/<phase>-<task>` internally. Contributor branches like `jcarranz/readme-enhancements-01` are fine; note the branch name in the notes section if it deviates from the `codex/` pattern.
5. **Context over code** — explain *why* the change was needed. Maintainers care most about the user pain that motivated the contribution, not the file list.
6. **No trailing apologies or placeholders** — state what was done confidently and invite feedback with a question.
7. **No em dashes (—)** — use commas, semicolons, colons, or restructure the sentence.

---

## Open source PR best practices (pycro-specific)

1. **Friendly intro for external contributors** — link back to how you found the project or what motivated the PR. Linkfy shares progress publicly (videos, etc.); referencing that context builds trust.
2. **Reference the commit or PR that your work continues** — if your change extends a recent commit (e.g. `docs(readme): improve quickstart`), name it so the maintainer sees the thread.
3. **One logical change per PR** — the description should reflect a focused scope. If the diff spans unrelated concerns, say so upfront.
4. **Explicit testing evidence** — describe what you ran or manually verified. Even for docs PRs, note that you followed the steps yourself and hit (or confirmed fixing) the friction point.
5. **Flag convention choices** — if you inferred a convention from history (commit prefix, branch name, file location), say so. The project has no CONTRIBUTING.md yet, so showing your reasoning helps.
6. **Keep sections scannable** — headings per logical group, short paragraphs, no long bullet lists. Maintainers skim before they read.
7. **Link related issues or prior PRs** — use `#number` for GitHub auto-links when following up on something.

---

## Steps

### 1. Detect current branch

Run:
```bash
git branch --show-current
```

If the current branch is `main`, stop immediately and tell the user:

> "You are on the `main` branch. Please switch to a feature or fix branch before generating a PR description. There is nothing to compare against `main` from here."

Do not proceed further.

---

### 2. Verify commits exist on the branch

Get all commits on the current branch that are not on main:
```bash
git log main..HEAD --format="%H %s"
```

If the output is empty (no commits), stop and tell the user:

> "The branch `<branch-name>` has no commits ahead of `main` yet. Please make and commit your changes before generating a PR description."

Do not proceed further.

---

### 3. Ask the user for PR context

Before analyzing the diff, ask the user:

> "Before I draft the PR description, could you give me some context?
>
> - Is this a **bug fix**, **new feature**, **documentation update**, **refactor**, or something else?
> - What was the problem or motivation that led to this change? A short sentence or two is enough, or you can share a path to a `.md` file with more details.
>
> (If you already have a GitHub issue number, share it and I will reference it in the description.)"

Wait for the user's answer before proceeding. If the user provides a `.md` file path, read that file and use its contents as context for the description.

---

### 4. Gather the committed diff

Get the full diff of all **committed** changes (do not include uncommitted or staged-only files):
```bash
git diff main..HEAD
```

Get only the list of changed files and their status:
```bash
git diff main..HEAD --name-status
```

Also look at recent commits on main to confirm the scope/type convention in use:
```bash
git log main --oneline -20
```

---

### 5. Identify new files and ask the user

From the `--name-status` output, separate files by status:
- **Modified (M):** always include in the analysis
- **Deleted (D):** always include in the analysis
- **Renamed (R):** always include in the analysis
- **Added (A):** do NOT include by default

If there are any added (A) files, ask the user before including them:

> "I found the following new files in the diff. Would you like to include them in the PR description? I am skipping them by default since they are often local scratch files.
>
> - `path/to/new_file.py`
> - `path/to/another_file.md`"

Wait for the user's answer before proceeding.

---

### 6. Pick the PR title

Use the Conventional Commits format:

```
<type>(<scope>): <short description>
```

- Pick `type` from: `feat`, `fix`, `docs`, `chore`, `ci`, `refactor`, `perf`, `style`, `test`, `build`
- Pick `scope` from the changed area (e.g. `readme`, `runtime`, `input`, `ci`, `build`)
- Keep the subject under 72 characters
- Use imperative mood: "add", "fix", "clarify" — not "added", "fixing"

---

### 7. Draft the PR description

Using the diff, commit history, the user's context from step 3, and the conventions above, produce a PR description with this structure:

```
<type(scope): short description>

<2-4 sentence intro. Mention how you found the project or what motivated the PR. If this follows up on
a specific commit or prior PR, name it explicitly. Keep it warm and brief.>

---

## What changed and why

### <Group 1: logical area of change>

<Explain what changed and why the user needed it. Lead with the problem, then the fix. Focus on user
pain or missing context, not on file names.>

### <Group 2: another logical area>

<Explanation.>

... (one section per logical group of changes)

---

## Testing

<Describe how you verified the change. For docs PRs: confirm you followed the steps yourself and hit
(or confirmed the fix of) the friction. For code PRs: list commands run and output observed.
If no automated tests cover this, say so and describe the manual check.>

---

## Notes for reviewers

<Flag: convention choices (commit prefix used, branch naming), open questions, anything you inferred
from history since there is no CONTRIBUTING.md yet. Also note if the branch name deviates from the
maintainer's codex/<phase>-<task> convention. Invite the reviewer to correct anything you missed.
Omit this section only if there is truly nothing to flag.>
```

Guidelines for the description body:
- Write for GitHub's markdown renderer: do NOT hard-wrap lines. Each paragraph or bullet is a single long line.
- Group changes by logical area, not by file.
- Lead each section with the problem that motivated the change, then the fix.
- Use plain language and short sentences.
- Do NOT use em dashes (—). Use commas, semicolons, colons, or rewrite the sentence.
- Do not list file names unless they are directly relevant to understanding the change.
- Keep the intro short: 2-4 sentences max.
- Apply all seven pycro-specific best practices from the top of this skill.

---

### 8. Save the description to a file

After drafting the description, save it to:

```
pr-description.md
```

at the repo root.

Tell the user:
> "I saved the description to `pr-description.md` at the repo root. You can open it, copy the contents, and paste directly into GitHub's PR body field."

Do NOT commit this file. If `pr-description.md` already exists, overwrite it without asking.

---

### 9. Present and offer refinements

Show the draft inline in the chat as well, then ask:
- "Does this capture everything? Let me know if you want to adjust the tone, add more detail to any section, or change the title. Once you are happy with it, `pr-description.md` is ready to paste into GitHub."
