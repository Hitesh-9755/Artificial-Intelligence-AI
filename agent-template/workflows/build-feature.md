# Workflow: Build Feature

Execute this standardized workflow for every feature or task.

---

### Phase 0 — Clarify & State Archive
1. **Archive Previous State**: If `state.json` has an existing `task_id` that is completed or active, copy the current `state.json` to `.agent/history/<previous-task_id>.json` before proceeding. This ensures prior task history is never overwritten or lost.
2. **Restate Request**:
   - **User Story** (`As a... I want to... So that...`)
   - **Acceptance Criteria** (concrete testable conditions)
   - **Assumptions**
   - **`scope_files`** (explicit list of files allowed to be created or modified for this specific feature only)
3. **Persist State**: Save the new feature state directly into `state.json`.
4. **Non-Blocking**: Do not wait for user approval — proceed immediately to Phase 1.

---

### Phase 1 — Plan
- Deconstruct the feature into **3 to 7 atomic, ordered steps**.
- For each step, define:
  - Step title & objective
  - Target files (strictly within `scope_files`)
  - Done condition (how to verify step completion)
- Persist the structured plan into `state.json`.

---

### Phase 2 — Build
For each step in the plan:
1. **Read `inbox.md`**: Check for any new user guidance. If present, incorporate it and record it in `state.json` under `inbox_applied`.
2. **Git Checkpoint**: Ensure working tree status is tracked before making edits.
3. **Smallest Change**: Make the minimal correct code change strictly within `scope_files`.
4. **Verification**: Run the commands configured in `config.json` (`typecheck_command`, `lint_command`, `test_command`).
5. **Log Output**: Save raw terminal output of each command execution in `logs/<task-id>-step-<step-number>.log`.
6. **Git Commit**: Commit the change with a clear, concise message describing what was done.

#### Midpoint Check
- Halfway through the planned steps, pause and compare the current state with the initial acceptance criteria in `state.json`.
- Fix any scope creep or behavioral drift before continuing remaining steps.

---

### Phase 3 — Self Review
- Run the **FULL test suite** (existing + newly added tests), not just tests for the current feature.
- Inspect the git diff against acceptance criteria.
- Explicitly check and flag:
  - Weakened or deleted assertions/tests
  - Hardcoded secrets, credentials, or environment variables
  - Any changes made outside `scope_files`

---

### Phase 4 — Report
Generate a detailed report saved at `reports/<task-name>.md` with the following mandatory sections:
1. **Summary**: Plain-language overview of what was implemented.
2. **Acceptance Criteria**: Each criterion marked as Pass or Fail with concrete evidence.
3. **Files Changed**: Ordered reading list of changed files with a concise explanation for each.
4. **Important Decisions**: Why this approach was chosen vs what alternatives were evaluated.
5. **Concepts to Learn**: Explain any new patterns, architectural decisions, or libraries at a fresher/junior-developer level.
6. **Assumptions & Risks**: Explicit assumptions made during execution and any lingering operational risks.
7. **Open Questions**: Doubts faced during development along with the safe default chosen.
8. **Test Results**: Commands executed, outcomes, and links to corresponding raw files in `logs/`.
9. **Self-Check Questions**: 3 to 5 scenario-based questions for the user to test their understanding.
10. **Next Steps**: Recommended follow-ups, refactoring, or complementary features.

---

### Phase 5 — Feedback
- When the user reviews the report and provides feedback, implement fixes on the **same git branch**.
- If the user rejects an approach, record the rejected direction in `state.json` under `rejected_feedback` to ensure the agent never repeats that pattern in future iterations.
