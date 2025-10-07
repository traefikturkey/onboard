---
description: 'Guidelines for creating and maintaining GitHub Copilot instruction, prompt, and chat mode files with current best practices and supported features.'
applyTo: '.github/{instructions/**/*.instructions.md,prompts/**/*.prompt.md,chatmodes/**/*.chatmode.md}'
---

# Copilot Customization Instructions

When editing Copilot customization files, anchor changes in current Microsoft guidance and our workspace guardrails.

## Refer to these resources first
- [Customize chat to your workflow](https://code.visualstudio.com/docs/copilot/customization/overview)
- [Set up a context engineering flow in VS Code](https://code.visualstudio.com/docs/copilot/guides/context-engineering-guide)
- [Use `.instructions.md` files](https://code.visualstudio.com/docs/copilot/customization/custom-instructions#_use-instructionsmd-files)
- [Create reusable prompt files](https://code.visualstudio.com/docs/copilot/customization/prompt-files)
- [Create custom chat modes](https://code.visualstudio.com/docs/copilot/customization/custom-chat-modes)
- [Community examples](https://github.com/github/awesome-copilot)

## Research checklist
- Scan documentation and release notes for new features or deprecations.
- Confirm supported frontmatter fields, metadata, and formatting for the target artifact.
- Validate sample snippets before reusing them verbatim.

## Authoring checklists

### Instruction files (`*.instructions.md`)
- Capture only repo-specific guardrails; link out to broader guidance.
- Keep directives short, declarative, and actionable.
- Note naming, tooling, or review expectations Copilot must respect.

### Prompt files (`*.prompt.md`)
- Focus on one repeatable workflow with explicit steps.
- Declare required chat mode, tools, or context in frontmatter.
- Ensure prompts complement existing instructions without conflict.

### Chat modes (`*.chatmode.md`)
- Define persona, responsibilities, guardrails, and success criteria up front.
- Configure `tools`, `mode`, and optional `model` conservatively.
- Outline deterministic workflow steps and reference supporting artifacts.

## Workspace-wide instructions
- Treat `.github/copilot-instructions.md` as the global rule set; updates affect every chat.
- Keep global guardrails concise and defer specifics to scoped instruction files.
- Note the rationale for global changes in PR descriptions or commit messages.

## Maintenance reminders
- Revisit linked documentation whenever workflows or Copilot capabilities change.
- Retire or refactor guidance that conflicts, drifts, or falls out of use.
- Gather feedback from users and adjust instructions accordingly.
