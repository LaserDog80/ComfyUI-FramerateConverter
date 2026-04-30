# CLAUDE.md

<!-- Rename this file to CLAUDE.md in the target repo so Claude Code
     auto-loads it. -->

## Project

<TODO: one-line description of this project.>

## Required reading before any ComfyUI work

**Before writing or modifying any ComfyUI custom-node code in this repo,
read `comfy-gotchas.md` end to end.** It documents non-obvious traps in
the ComfyUI node API, the FFmpeg filters commonly used from custom
nodes, and the Comfy Registry publish workflow. Many of these are silent
failures — wrong audio pitch, wrong fps, the wrong container being saved
— that look correct until a user notices.

## Releasing fixes

The Comfy Registry only republishes when `pyproject.toml` changes on
`main`. End any user-visible fix with a version bump in `pyproject.toml`
— merging to `main` alone does not ship the change to users on the
Manager stable channel.

## Keeping the gotchas current

When you hit and fix a non-obvious ComfyUI or FFmpeg trap that isn't
already in `comfy-gotchas.md`, add it. The doc stays useful only if it
stays current. Each entry should follow the existing format: a tight
trap → symptom → correct pattern, with a small generic code snippet
where it helps.
