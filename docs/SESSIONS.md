# How sessions work together

Sessions (a chat, a terminal Claude Code session, a VS Code session) do not share memory or history.
The repo and GitHub are the only shared record. Coordination happens through files and pull requests.

## Roles

**Manager session.** One at a time. It does not write feature code.

- Breaks the plan into tasks and writes a task file for each, with acceptance criteria.
- Owns `docs/TASKS.md` (the board). Only the manager edits it.
- Reviews each worker pull request against the task's acceptance criteria and the rules in `CLAUDE.md`.
- Runs the checks itself where it can (tests, a backtest re-run). It does not accept "done" on a worker's word.
- Marks a task Done only after Sujay merges the pull request.
- Raises decisions that belong to Sujay instead of making them.

**Worker session.** Any number, one task each.

- Takes one task whose status is Ready, on its own branch.
- Edits only its own task file in `docs/tasks/`, never the board.
- Finishes by updating the task file and opening a pull request.
- If blocked, writes the blocker in the task file, pushes, and stops.

## Task lifecycle

`Ready` -> `In progress` -> `In review` -> `Done`, or `Blocked` at any point.

- Manager writes the task file and adds it to the board as Ready.
- Worker sets its task file to In progress, does the work, opens a PR, sets In review.
- Manager reviews. Changes needed: back to In progress with notes in the task file. Accepted: tells Sujay it is ready to merge.
- After the merge the manager sets Done on the board.

## Avoiding conflicts

- The board has one editor (the manager). Each task file has one editor at a time (its worker, then the manager during review).
- Two workers never share a branch or a task.
- Tasks that touch the same files are run one after another, not in parallel. The manager records this in "Depends on".
