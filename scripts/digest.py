#!/usr/bin/env python3
"""Condense Claude Code session transcripts into a markdown digest.

Reads the JSONL transcripts Claude Code keeps under ~/.claude/projects/
for the current working directory, and prints a per-session digest:
what the user asked, what Claude said at key moments, which files were
changed, which commands ran.

Stdlib only. No arguments needed for normal use:

    python3 digest.py           digest of sessions not yet recorded
    python3 digest.py --list    all sessions with new/recorded status
    python3 digest.py --all     digest everything, ignore the state file
    python3 digest.py --mark    record current sessions as processed

State lives in docs/.vibediary-state.json inside the project.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# Caps so one huge session cannot flood the digest.
MAX_PROMPTS = 30
PROMPT_CHARS = 400
MAX_HIGHLIGHTS = 20
HIGHLIGHT_CHARS = 300
MIN_HIGHLIGHT_CHARS = 80
MAX_FILES = 40
MAX_COMMANDS = 20
COMMAND_CHARS = 140

SKIP_COMMANDS = ("ls", "ls ", "pwd", "cd ", "cat ", "head ", "tail ", "which ")


def project_transcript_dir(cwd):
    encoded = re.sub(r"[^A-Za-z0-9]", "-", cwd)
    return os.path.join(os.path.expanduser("~"), ".claude", "projects", encoded)


def state_path(cwd):
    return os.path.join(cwd, "docs", ".vibediary-state.json")


def load_state(cwd):
    try:
        with open(state_path(cwd)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"sessions": {}}


def save_state(cwd, state):
    path = state_path(cwd)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=1)


def iter_records(path):
    with open(path, errors="replace") as f:
        for line in f:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def is_real_prompt(rec):
    """True for messages the human actually typed."""
    if rec.get("type") != "user" or rec.get("isMeta") or rec.get("isSidechain"):
        return False
    content = rec.get("message", {}).get("content")
    if isinstance(content, list):
        texts = [b.get("text", "") for b in content if b.get("type") == "text"]
        content = "\n".join(t for t in texts if t)
    if not isinstance(content, str) or not content.strip():
        return False
    # Skill/command plumbing arrives as user messages wrapped in XML tags.
    return not content.lstrip().startswith("<")


def prompt_text(rec):
    content = rec.get("message", {}).get("content")
    if isinstance(content, list):
        content = "\n".join(b.get("text", "") for b in content if b.get("type") == "text")
    return " ".join(content.split())


def clip(text, limit):
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def sample(items, limit):
    """Up to `limit` items spread evenly across the list, order kept."""
    if len(items) <= limit:
        return items
    step = len(items) / limit
    return [items[int(i * step)] for i in range(limit)]


def parse_session(path):
    """One pass over a transcript -> dict of everything the digest needs."""
    prompts = []
    highlights = []
    files = {}  # path -> edit count
    commands = []
    first_ts = last_ts = None
    lines = 0

    for rec in iter_records(path):
        lines += 1
        ts = rec.get("timestamp")
        if ts:
            first_ts = first_ts or ts
            last_ts = ts
        if is_real_prompt(rec):
            prompts.append(prompt_text(rec))
        elif rec.get("type") == "assistant" and not rec.get("isSidechain"):
            for block in rec.get("message", {}).get("content", []):
                btype = block.get("type")
                if btype == "text":
                    text = " ".join(block.get("text", "").split())
                    if len(text) >= MIN_HIGHLIGHT_CHARS:
                        highlights.append(text)
                elif btype == "tool_use":
                    name = block.get("name", "")
                    inp = block.get("input", {})
                    if name in ("Edit", "Write", "NotebookEdit"):
                        fp = inp.get("file_path") or inp.get("notebook_path")
                        if fp:
                            files[fp] = files.get(fp, 0) + 1
                    elif name == "Bash":
                        cmd = " ".join(inp.get("command", "").split())
                        if cmd and not cmd.startswith(SKIP_COMMANDS):
                            commands.append(cmd)

    return {
        "prompts": prompts,
        "highlights": highlights,
        "files": files,
        "commands": commands,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "lines": lines,
    }


def fmt_ts(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, AttributeError):
        return "unknown time"


def render_session(session_id, data, updated=False):
    out = []
    tag = " (updated: this session grew since it was last recorded)" if updated else ""
    out.append("## Session %s%s" % (session_id[:8], tag))
    out.append("From %s to %s" % (fmt_ts(data["first_ts"]), fmt_ts(data["last_ts"])))
    out.append("")

    prompts = data["prompts"]
    out.append("### What the user asked (in order)")
    for p in sample(prompts, MAX_PROMPTS):
        out.append("- " + clip(p, PROMPT_CHARS))
    if len(prompts) > MAX_PROMPTS:
        out.append("- (showing %d of %d prompts, sampled evenly)" % (MAX_PROMPTS, len(prompts)))
    out.append("")

    highlights = data["highlights"]
    if highlights:
        out.append("### What Claude said (key moments, in order)")
        for h in sample(highlights, MAX_HIGHLIGHTS):
            out.append("- " + clip(h, HIGHLIGHT_CHARS))
        if len(highlights) > MAX_HIGHLIGHTS:
            out.append("- (showing %d of %d, sampled evenly)" % (MAX_HIGHLIGHTS, len(highlights)))
        out.append("")

    files = data["files"]
    if files:
        out.append("### Files created or edited")
        for fp, count in list(files.items())[:MAX_FILES]:
            out.append("- %s (%d change%s)" % (fp, count, "s" if count > 1 else ""))
        if len(files) > MAX_FILES:
            out.append("- (and %d more files)" % (len(files) - MAX_FILES))
        out.append("")

    commands = data["commands"]
    if commands:
        seen = []
        for c in commands:
            if c not in seen:
                seen.append(c)
        out.append("### Commands run")
        for c in sample(seen, MAX_COMMANDS):
            out.append("- `%s`" % clip(c, COMMAND_CHARS))
        if len(seen) > MAX_COMMANDS:
            out.append("- (showing %d of %d distinct commands)" % (MAX_COMMANDS, len(seen)))
        out.append("")

    return "\n".join(out)


def find_sessions(tdir):
    try:
        names = sorted(f for f in os.listdir(tdir) if f.endswith(".jsonl"))
    except OSError:
        return None
    return [os.path.join(tdir, n) for n in names]


def main():
    cwd = os.getcwd()
    tdir = project_transcript_dir(cwd)
    paths = find_sessions(tdir)

    if paths is None:
        print("No Claude Code transcripts found for this project.")
        print("Expected them in: %s" % tdir)
        print("Have you used Claude Code in this folder before?")
        return
    if not paths:
        print("Transcript folder exists but holds no sessions yet: %s" % tdir)
        return

    state = load_state(cwd)
    recorded = state.get("sessions", {})
    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    sessions = []  # (id, path, data, status)
    for path in paths:
        session_id = os.path.basename(path)[:-6]
        data = parse_session(path)
        if not data["prompts"]:
            status = "empty"
        elif session_id not in recorded:
            status = "new"
        elif data["lines"] > recorded[session_id].get("lines", 0):
            status = "updated"
        else:
            status = "recorded"
        sessions.append((session_id, path, data, status))

    # Oldest first, so the diary reads in the order things happened.
    sessions.sort(key=lambda s: s[2]["first_ts"] or "")

    if mode == "--list":
        for session_id, _path, data, status in sessions:
            print("%s  %s  %3d prompts  %s" % (
                session_id[:8], fmt_ts(data["first_ts"]), len(data["prompts"]), status))
        return

    if mode == "--mark":
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for session_id, _path, data, status in sessions:
            if status in ("new", "updated"):
                recorded[session_id] = {"lines": data["lines"], "digested": now}
        state["sessions"] = recorded
        save_state(cwd, state)
        print("Recorded %d session(s) in %s" % (len(recorded), state_path(cwd)))
        return

    if mode == "--all":
        todo = [s for s in sessions if s[3] != "empty"]
    else:
        todo = [s for s in sessions if s[3] in ("new", "updated")]

    if not todo:
        print("Nothing new to record: every session with real activity is already in the diary.")
        return

    print("# vibediary digest: %d session(s) to record\n" % len(todo))
    for session_id, _path, data, status in todo:
        print(render_session(session_id, data, updated=(status == "updated")))


if __name__ == "__main__":
    main()
