---
name: create-skills
description: >
  Creates standardized OpenCode skills following the agentskills.io specification.
  Use when you need to create a new skill, restructure existing skills, or ensure
  skills follow the correct format. This skill creates proper directory structure,
  SKILL.md with frontmatter, and optional reference files.
metadata:
  version: "1.0"
---

## When to Use

Use this skill when:
- Creating a new skill for the project
- Restructuring existing skills
- Validating skill format compliance
- User asks to create/define a skill

## Instructions

### Step 1: Define Skill Metadata

Collect or ask user for:
- **name**: lowercase letters, numbers, hyphens only (1-64 chars), no leading/trailing hyphens
- **description**: 1-1024 chars, describe what it does and when to use it
- **license** (optional): license name
- **compatibility** (optional): environment requirements
- **metadata** (optional): key-value pairs like version, author

### Step 2: Create Directory Structure

Create skill directory in `.opencode/skills/<skill-name>/`:

```
.opencode/skills/<skill-name>/
├── SKILL.md              # Required
├── references/           # Optional
│   └── REFERENCE.md     # Optional detailed docs
├── scripts/              # Optional
└── assets/               # Optional
```

### Step 3: Write SKILL.md

Use this template:

```markdown
---
name: <skill-name>
description: >
  <Description in 1-1024 characters. Include what it does and when to use it.>
metadata:
  version: "1.0"
---

## Instructions

<Step-by-step instructions for the skill>

## Examples

<Input/Output examples if helpful>

## Rules

<Any constraints or rules>
```

### Step 4: Validate

Check:
- Name matches directory name (lowercase, hyphens only)
- Description is 1-1024 characters
- Frontmatter has required fields: name, description
- No consecutive hyphens in name

## Reference

See https://agentskills.io/specification for full specification.
See https://opencode.ac.cn/docs/skills/ for OpenCode-specific requirements.

Key rules:
- name: `^[a-z0-9]+(-[a-z0-9]+)*$`
- Path: `.opencode/skills/<name>/SKILL.md`
- Fields: name (required), description (required), license, compatibility, metadata
