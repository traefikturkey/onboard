# Prompt Automation Feature

## Overview
Create a reusable prompt that can replicate the instruction improvement workflow across any project type. This prompt should analyze conversation history, identify patterns, consolidate improvements, and implement changes across the instruction ecosystem without being tied to specific technologies.

## Goal
Generate `.github/prompts/update-instructions.prompt.md` that contains a comprehensive, generic prompt for automated instruction improvements based on conversation history analysis that can be used across Python, JavaScript, Go, Rust, Docker, or any other project types.

## Context
We completed a manual process that:
1. Analyzed conversation history files in `.specstory/history/*.md`
2. Identified 14 common interaction issues
3. Consolidated improvements into actionable patterns
4. Updated 7 instruction files with project-specific approaches
5. Created VERSION timestamp for tracking
6. Verified all changes with tests

The resulting prompt has been generalized to work with any technology stack or project type.

## Deliverables
- Feature specification document
- Step-by-step implementation plan
- Comprehensive **generic** prompt file at `.github/prompts/update-instructions.prompt.md`
- Documentation for future usage across different project types

## Success Criteria
The generated prompt should be able to:
- Recreate the entire instruction improvement workflow for any project type
- Analyze new conversation history since last VERSION timestamp or entire history if no VERSION file exists
- Apply consolidated improvement patterns systematically regardless of technology stack
- Maintain consistency with any project's instruction file ecosystem
- Include proper verification and testing steps appropriate for the project type
- Work effectively for Python, JavaScript, Docker, Rust, Go, or any other technology stack
