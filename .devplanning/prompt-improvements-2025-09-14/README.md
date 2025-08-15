
# Original Prompt
```
- create a new feature directory at .devplanning/prompt-improvements-2025-09-14/
- in that directory create a interaction-issues.md file
- analyze each file in .specstory/history/*.md one by one, for each history file do the following:
    - create a header section in the interaction-issues.md file, uses the filename for the text of this header
    - provide a very brief and concise summary of the file's content
    - Note any issues that occurred between the user and the AI
    - Note any issues or problems that the AI encountered solving the users request
- Once you have completed analyzing all to the history files:
    - create a new file .devplanning/prompt-improvements-2025-09-14/determined-issues.md
    - add a header for `Existing Instructions Summary`
    - review the existing .github/copilot-instructions.md and each of the files in .github/instructions/*.instructions.md one by one:
      - add a section at the top of the determined-issues.md for each file with the filename as the header and the following subsections:
        - the file types if any that the file applyTo header is using
        - a brief description of the file's purpose and content
    - add a header for `Common Interaction Issues`
    - review the interaction-issues.md file looking for common problems
    - in the determined-issues.md create a section for each common problem
    - that problem section should have the following subsections
        - a brief description of the problem 
        - a suggested prompt instructions to address the problem
        - the .github/**/*.md file that makes the most sense to add the suggested prompt instruction to based on the file types that are involved in the problem
```

# Follow up Prompt

```
- create a directory .devplanning/prompt-improvements-2025-09-14/specstory_history_checkpoint and move the .specstory/history/*.md files into it 
- suggest