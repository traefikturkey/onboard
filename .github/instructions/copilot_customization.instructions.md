---
description: 'Guidelines for creating and maintaining GitHub Copilot instruction, prompt, and chat mode files with current best practices and supported features.'
applyTo: '.github/{instructions/**/*.instructions.md,.github/copilot-instructions.md}'
---

# Copilot Customization Instructions

When editing Copilot customization files, anchor changes in current Microsoft guidance and our workspace guardrails.

## Workspace-wide instructions
- Treat `.github/copilot-instructions.md` as the global rule set; updates affect every chat.
- Keep global guardrails concise and defer specifics to scoped instruction files.
- Note the rationale for global changes in PR descriptions or commit messages.

## Refer to these resources first
- [Customize chat to your workflow](https://code.visualstudio.com/docs/copilot/customization/overview)
- [Set up a context engineering flow in VS Code](https://code.visualstudio.com/docs/copilot/guides/context-engineering-guide)
- [Use `.instructions.md` files](https://code.visualstudio.com/docs/copilot/customization/custom-instructions#_use-instructionsmd-files)
- [Community examples](https://github.com/github/awesome-copilot)

### Instruction files (`*.instructions.md`)
- Capture only repo-specific guardrails; link out to broader guidance.
- Keep directives short, declarative, and actionable.
- Note naming, tooling, or review expectations Copilot must respect.

## Maintenance reminders
- Revisit linked documentation whenever workflows or Copilot capabilities change.
- Retire or refactor guidance that conflicts, drifts, or falls out of use.
- Gather feedback from users and adjust instructions accordingly.
