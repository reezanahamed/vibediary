---
name: vibediary
description: Turn Claude Code sessions into a plain-English project diary, a living how-it-works doc, and a visual map. Use when the user runs /vibediary or asks to update the project diary, document the journey, or explain what happened in past sessions.
---

# vibediary

You are writing the story of this project for its own builder. They built it with AI, fast, and the reasoning lives in old sessions they will never reread. Your job: turn those sessions into three documents a beginner could follow. Write everything in plain English. If a technical term is unavoidable, gloss it in a few words the first time. Be honest: failures, dead ends, and reversals belong in the diary, they are the most useful part.

Never include em-dashes in anything you write here.

## Step 1: choose the output folder

vibediary must never damage a docs folder the user made for another purpose. Decide where to write, in this order:

1. `docs/.vibediary-state.json` exists: vibediary already owns `docs/`. Use `docs/`.
2. `docs/vibediary/.vibediary-state.json` exists: use `docs/vibediary/`.
3. `docs/` does not exist (or is empty): use `docs/`. When you create it, also create a `.gitignore` inside it containing just `*`. This keeps the diary out of git by default, since it can repeat private things from sessions. Create this file only when creating the folder; if the user deleted it later to publish their diary, never bring it back.
4. `docs/` exists with the user's own content: leave every existing file alone. Use `docs/vibediary/` instead, create it the same way as in rule 3, and tell the user why in your report.

Extra safety, whichever folder you use:
- Never overwrite a `diary.md`, `how-it-works.md`, or `map.html` that vibediary did not write. Its own files are recognizable: the diary starts with "The story of this project, taken from real Claude Code sessions", how-it-works has "by vibediary" near the top, the map contains VIBEDIARY markers. If a same-named foreign file is in the way, stop, explain, and ask the user what to do.
- If the project has a docs site config (`mkdocs.yml`, `docs/conf.py`, a docusaurus config), warn the user in your report: site builders publish everything in their source folder no matter what git ignores, so they should exclude the vibediary folder from the site build or move it.

Call the chosen folder OUT below.

## Step 2: digest the sessions

From the project root, run the digest script that lives next to this SKILL.md (normally `~/.claude/skills/vibediary/scripts/digest.py`):

```bash
python3 ~/.claude/skills/vibediary/scripts/digest.py --dir OUT
```

(`--dir OUT` can be dropped when OUT is `docs`.) It prints a condensed digest of every session not yet recorded: what the user asked, what Claude said at key moments, files changed, commands run.

- If it prints "Nothing new to record" AND `OUT/diary.md`, `OUT/how-it-works.md`, and `OUT/map.html` all exist, tell the user everything is current and stop.
- If it says no transcripts were found, tell the user plainly and stop.
- A session marked "updated" grew after it was last recorded: revise that session's existing diary entry instead of adding a duplicate.

## Step 3: understand the current code

Skim the repo as it is now: README if present, the main source files, `git log --oneline` if it is a git repo. You need this to write how-it-works truthfully and to name the real parts in the map. Do not deep-read everything; this is a skim for structure.

## Step 4: write or update OUT/diary.md

The diary is append-only, ordered oldest first. Start the file with:

```markdown
# Project diary

The story of this project, taken from real Claude Code sessions. Newest entry at the bottom.
```

For each session in the digest, append one entry:

```markdown
## 2026-07-03: short title naming what actually happened

What was asked, what got built, what broke and how it was fixed, and any
decision made along the way WITH its reason. Two to six short paragraphs
or bullets. Plain words. A stranger should understand it without opening
the code.
```

Rules:
- The WHY is the product. "Switched to X because Y kept failing" beats a feature list.
- Include real failures. "The gif was too slow and got rebuilt three times" is a good sentence.
- Merge trivial sessions (a one-line question, a quick fix) into a short entry; never pad.
- For an "updated" session, rewrite its existing entry to include the new events.

## Step 5: rewrite OUT/how-it-works.md

Rewrite this file completely every run from the digest, the diary, and the code skim. It explains the whole project to a smart beginner seeing it for the first time:

```markdown
# How this project works

Last updated 2026-07-05 by vibediary.

One paragraph: what this project is and what it does for its user.

## The parts

One short section per real part (file or folder), saying what it does and
why it exists. Plain English, glossed jargon.

## How a typical run flows

Numbered walk-through of what happens end to end when the project is used.

## Decisions that shaped it

The key WHY entries pulled from the diary, so a reader gets the reasoning
without reading the whole diary.
```

## Step 6: generate OUT/map.html

Copy `assets/map-template.html` (next to this SKILL.md) to `OUT/map.html`, then replace ONLY the JavaScript between the `VIBEDIARY:DATA-START` and `VIBEDIARY:DATA-END` markers with the real project:

- `name` and `tagline`: the project and what it does, one plain sentence.
- `columns`: 3 to 5 columns, ordered left to right in the order things happen (for example: what the user does, the engine, what comes out). Each node is a real part of the project with `label`, optional `sub` (a filename fits well), and `desc`: one or two plain-English sentences saying what it does and why it exists. 4 to 12 nodes total.
- `edges`: only the connections that help understanding.

Touch nothing outside the markers. The file must keep working offline: no external URLs, scripts, fonts, or images.

## Step 7: mark sessions as recorded

```bash
python3 ~/.claude/skills/vibediary/scripts/digest.py --mark --dir OUT
```

This writes `OUT/.vibediary-state.json` so the next run only picks up new sessions. Run it only after the docs are written.

## Step 8: report

Tell the user in a few lines: how many sessions were recorded, one interesting thing the diary now captures, and the three file paths. Suggest opening `OUT/map.html` in a browser. If the folder was newly created, mention it starts gitignored for privacy (delete `OUT/.gitignore` to commit the diary). Include any warning from step 1.
