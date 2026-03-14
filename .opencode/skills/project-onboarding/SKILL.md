---
name: project-onboarding
description: >
  Helps AI agents orient themselves when starting development tasks in large projects.
  Handles understanding project context, updating AGENTS.md, tracking development progress,
  and maintaining documentation. Use when starting new features, phases, fixing bugs,
  or whenever the project context needs clarification.
metadata:
  version: "1.0"
---

## Instructions

### Step 1: Understand Project Context

1. Read `AGENTS.md` for architecture, build commands, code style
2. Read relevant docs based on task type:
   - Architecture overview: `docs/anti-fomo核心.md`
   - API contracts: `docs/api.md`
   - Product roadmap: `docs/product-roadmap.md`
   - MVP scope: `docs/mvp-scope-v1.md`
   - Refactoring plan: `docs/refactoring-plan.md`
   - Docker deployment: `docker/README.md` or Makefile
   - Past bugs/accidents: `docs/accidents.md`

### Step 2: Update AGENTS.md if Needed

Check if AGENTS.md needs updates:
- Are build commands accurate?
- Are code style guidelines complete?
- Are there new important reminders (common bugs to avoid)?
- Is the documentation guide table up to date?

If updating AGENTS.md:
1. Keep it concise (~150 lines max)
2. Include: build/lint/test commands, code style, important reminders, docs guide
3. Move detailed historical info (bugs, progress) to `docs/accidents.md`

### Step 3: Track Development Progress

When significant progress is made:
1. Update `docs/todo-list.md` with completed items
2. Add new items to the appropriate development phase

### Step 4: Document New Learnings

If you encounter bugs or learn important lessons:
1. Add to `docs/accidents.md` with:
   - Date and context
   - Problem description
   - Root cause
   - Fix (code snippet if helpful)
   - How it was discovered

## Rules

- AGENTS.md should stay under 150 lines
- Detailed bugs/accidents go in docs/accidents.md
- Development progress goes in docs/todo-list.md
- Commit message format: lowercase imperative, no emoji
