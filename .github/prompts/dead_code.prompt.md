---
mode: agent
description: guides you through a systematic process to identify and safely remove dead code from the codebase using Vulture.
model: 'GPT-5 mini (Preview)'
---
# Dead Code Removal Prompt

## Procedure

Follow these steps when this prompt runs:

1. **Initialize cleanup**
   - Remove `.artifacts/vulture_files.md` if it exists

2. **Generate dead code report**
   - Run `make vulture` to identify potential dead code
   - If any files are output, place them as a checkboxed list into `.artifacts/vulture_files.md`

3. **Process each issue systematically**
   - Read `.artifacts/vulture_files.md` and work through the issues one by one

4. **For each dead code issue:**

   a. **Identify and run baseline tests**
      - Identify tests that exercise the file being processed
      - Run baseline tests using `uv run pytest <test_file_path>` to ensure they pass before removal
   
   b. **Remove the dead code**
      - Remove the dead code mentioned for the file line you are processing
   
   c. **Verify removal safety**
      - Rerun the tests to ensure no new failures caused by the removal
      - If there are errors: revert the dead code removal and mark the issue as unresolved
      - If tests pass: run `uv run python -m vulture <file_path> --min-confidence 60 --exclude=migrations` to verify the removal was successful
   
   d. **Update progress**
      - Mark the checkbox as completed if everything was successful
      - Move on to the next line of the file

5. **Continue until completion**
   - Process all lines until they have been checked or marked unresolved

## Notes

- Always run tests before and after each removal to ensure safety
- Revert any changes that cause test failures
- Use the vulture command to verify successful removals
- Mark unresolved issues clearly for future investigation
