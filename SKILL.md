---
name: vibediary
description: Turn Claude Code sessions into a plain-English project diary, a living how-it-works doc, and a visual map. Use when the user runs /vibediary or asks to update the project diary, document the journey, or explain what happened in past sessions.
---

# vibediary

You are writing the story of this project for its own builder. They built it with AI, fast, and the reasoning lives in old sessions they will never reread. Your job: turn those sessions into three documents a beginner could follow. Write everything in plain English. If a technical term is unavoidable, gloss it in a few words the first time. Be honest: failures, dead ends, and reversals belong in the diary, they are the most useful part.

Never include em-dashes in anything you write here.

## Step 1: digest the sessions

From the project root, run the digest script that lives next to this SKILL.md (normally `~/.claude/skills/vibediary/scripts/digest.py`):

```bash
python3 ~/.claude/skills/vibediary/scripts/digest.py
```

It prints a condensed digest of every session not yet recorded: what the user asked, what Claude said at key moments, files changed, commands run.

- If it prints "Nothing new to record" AND `docs/diary.md`, `docs/how-it-works.md`, and `docs/map.html` all exist, tell the user everything is current and stop.
- If it says no transcripts were found, tell the user plainly and stop.
- A session marked "updated" grew after it was last recorded: revise that session's existing diary entry instead of adding a duplicate.

## Step 2: understand the current code

Skim the repo as it is now: README if present, the main source files, `git log --oneline` if it is a git repo. You need this to write how-it-works truthfully and to name the real parts in the map. Do not deep-read everything; this is a skim for structure.

## Step 3: write or update docs/diary.md

Create `docs/` if needed. The diary is append-only, ordered oldest first. Start the file with:

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

## Step 4: rewrite docs/how-it-works.md

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

## Step 5: generate docs/map.html

Copy `assets/map-template.html` (next to this SKILL.md) to `docs/map.html`, then replace ONLY the JavaScript between the `VIBEDIARY:DATA-START` and `VIBEDIARY:DATA-END` markers with the real project:

- `name` and `tagline`: the project and what it does, one plain sentence.
- `columns`: 3 to 5 columns, ordered left to right in the order things happen (for example: what the user does, the engine, what comes out). Each node is a real part of the project with `label`, optional `sub` (a filename fits well), and `desc`: one or two plain-English sentences saying what it does and why it exists. 4 to 12 nodes total.
- `edges`: only the connections that help understanding.

Touch nothing outside the markers. The file must keep working offline: no external URLs, scripts, fonts, or images.

## Step 6: mark sessions as recorded

```bash
python3 ~/.claude/skills/vibediary/scripts/digest.py --mark
```

This writes `docs/.vibediary-state.json` so the next run only picks up new sessions. Run it only after the docs are written.

## Step 7: report

Tell the user in a few lines: how many sessions were recorded, one interesting thing the diary now captures, and the three file paths. Suggest opening `docs/map.html` in a browser.
