"""Repository rule checks, run by CI on every pull request.

Each check enforces a rule from CLAUDE.md. Exit code 1 if any check fails.

Inputs come from the environment so the script can also be run locally:
  BASE_REF   git ref to diff against (default: origin/main)
  PR_BRANCH  head branch name (default: current branch)
  PR_TITLE   pull request title (optional locally)
  PR_BODY    pull request description (optional locally)
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE_DIRS = ("common/", "markets/", "services/")
REQUIRED_DOCS = ("CLAUDE.md", "docs/PLAN.md", "docs/DECISIONS.md", "docs/TASKS.md", "docs/SESSIONS.md")
RULE_FILES = ("CLAUDE.md", ".github/", "tools/check_rules.py")
FORBIDDEN_SUFFIXES = (".parquet", ".csv", ".pkl", ".pickle", ".h5", ".hdf5", ".feather", ".npz", ".npy",
                      ".safetensors", ".gguf", ".pt", ".pth", ".onnx", ".bin", ".db", ".sqlite")
MAX_FILE_BYTES = 1_000_000
BRANCH_RE = re.compile(r"^task/T-(\d{3,})-[a-z0-9][a-z0-9-]*$")
TASK_FILE_RE = re.compile(r"^docs/tasks/T-(\d{3,})-[a-z0-9-]+\.md$")
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "Telegram bot token": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
    "Anthropic or OpenAI key": re.compile(r"\bsk-[A-Za-z0-9_-]{32,}\b"),
    "assigned secret": re.compile(
        r"(?i)\b(api[_-]?key|api[_-]?secret|secret[_-]?key|access[_-]?token|auth[_-]?token|password|totp[_-]?secret)\b"
        r"\s*[:=]\s*['\"][A-Za-z0-9+/_\-]{16,}['\"]"),
}
STYLES = ("positional", "swing", "intraday")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def tracked_files() -> list[str]:
    return [f for f in git("ls-files").splitlines() if f]


def changed_files(base: str) -> list[tuple[str, str]]:
    """(status, path) for files changed between the merge base and HEAD."""
    out = git("diff", "--name-status", "--no-renames", f"{base}...HEAD")
    rows = []
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        if path:
            rows.append((status.strip(), path.strip()))
    return rows


# ---------- checks on the whole tree ----------

def check_required_docs(files: list[str]) -> list[str]:
    errs = []
    for doc in REQUIRED_DOCS:
        p = ROOT / doc
        if not p.is_file() or p.stat().st_size == 0:
            errs.append(f"required doc missing or empty: {doc}")
    return errs


def check_forbidden_files(files: list[str]) -> list[str]:
    errs = []
    for f in files:
        name = f.rsplit("/", 1)[-1]
        if name == ".env" or name.startswith(".env."):
            if name != ".env.example":
                errs.append(f"secret file committed: {f}")
        if f.lower().endswith(FORBIDDEN_SUFFIXES):
            errs.append(f"data or model file committed: {f}")
        p = ROOT / f
        if p.is_file() and p.stat().st_size > MAX_FILE_BYTES:
            errs.append(f"file larger than {MAX_FILE_BYTES // 1000} kB: {f}")
    return errs


def check_secrets(files: list[str]) -> list[str]:
    errs = []
    for f in files:
        p = ROOT / f
        if not p.is_file() or p.stat().st_size > MAX_FILE_BYTES or f == "tools/check_rules.py" or f.startswith("tests/tools/"):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pat in SECRET_PATTERNS.items():
            m = pat.search(text)
            if m:
                line = text.count("\n", 0, m.start()) + 1
                errs.append(f"possible {label} in {f}:{line}")
    return errs


def module_of(path: str) -> tuple[str, ...]:
    """Ownership key of a python file: ('common',), ('markets','india','swing'), ('research',), ..."""
    parts = path.split("/")
    if parts[0] == "markets" and len(parts) >= 3:
        return ("markets", parts[1], parts[2])
    return (parts[0],)


def imports_of(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(node.lineno, a.name) for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append((node.lineno, node.module))
    return found


def import_violation(owner: tuple[str, ...], target: str) -> str | None:
    t = tuple(target.split("."))
    top = t[0]
    if top == "research" and owner[0] != "research":
        return "nothing may import from research/"
    if owner[0] == "common" and top in ("markets", "services"):
        return "common/ must not import from markets/ or services/"
    if owner[0] == "markets":
        if top == "services":
            return "markets/ must not import from services/"
        if top == "markets" and len(t) >= 2:
            if t[1] != owner[1]:
                return f"markets/{owner[1]} must not import from markets/{t[1]}"
            if len(t) >= 3 and owner[2] in STYLES and t[2] in STYLES and t[2] != owner[2]:
                return f"strategy module '{owner[2]}' must not import strategy module '{t[2]}'"
            if len(t) >= 3 and owner[2] == "adapters" and t[2] in STYLES:
                return "adapters must not import strategy modules"
    return None


def check_import_boundaries(files: list[str]) -> list[str]:
    errs = []
    for f in files:
        if not f.endswith(".py") or not f.startswith(("common/", "markets/", "services/")):
            continue
        try:
            imps = imports_of(ROOT / f)
        except SyntaxError as e:
            errs.append(f"syntax error in {f}: {e.msg} (line {e.lineno})")
            continue
        owner = module_of(f)
        for lineno, target in imps:
            why = import_violation(owner, target)
            if why:
                errs.append(f"{f}:{lineno} imports '{target}': {why}")
    return errs


# ---------- checks on the pull request ----------

def check_branch_name(branch: str) -> list[str]:
    if not BRANCH_RE.match(branch):
        return [f"branch '{branch}' must be named task/T-<number>-<short-name>, for example task/T-002-survivor-free-data"]
    return []


def check_task_file(branch: str, changes: list[tuple[str, str]]) -> list[str]:
    m = BRANCH_RE.match(branch)
    if not m:
        return []
    tid = m.group(1)
    touched = [p for _, p in changes if TASK_FILE_RE.match(p)]
    own = [p for p in touched if TASK_FILE_RE.match(p).group(1) == tid]
    errs = []
    if not own:
        errs.append(f"the task file docs/tasks/T-{tid}-*.md must be updated in this pull request (status and worker notes)")
    others_modified = [p for s, p in changes if TASK_FILE_RE.match(p) and TASK_FILE_RE.match(p).group(1) != tid and s != "A"]
    if others_modified:
        errs.append("one task per pull request: this PR modifies other tasks' files: " + ", ".join(others_modified))
    return errs


def check_docs_with_code(changes: list[tuple[str, str]]) -> list[str]:
    code = [p for _, p in changes if p.startswith(CODE_DIRS) and p.endswith(".py")]
    docs = [p for _, p in changes if p.startswith("docs/") or p in ("CLAUDE.md", "README.md")]
    if code and not docs:
        return ["code changed under common/, markets/ or services/ but no doc changed; update the docs in the same pull request"]
    return []


def check_tests_with_code(changes: list[tuple[str, str]], body: str) -> list[str]:
    code = [p for s, p in changes if p.startswith(CODE_DIRS) and p.endswith(".py") and s != "D" and not p.endswith("__init__.py")]
    tests = [p for _, p in changes if p.startswith("tests/") and p.rsplit("/", 1)[-1].startswith("test_")]
    if code and not tests and not re.search(r"(?im)^\s*no-test-reason\s*:\s*\S+", body or ""):
        return ["code changed without a test; add a test or put a line 'No-test-reason: <why>' in the PR description"]
    return []


def check_rules_change(changes: list[tuple[str, str]], title: str) -> list[str]:
    touched = [p for _, p in changes if p.startswith(RULE_FILES) or p in RULE_FILES]
    if touched and not (title or "").lower().startswith("[rules]"):
        return ["this PR changes the rules (" + ", ".join(sorted(touched)[:4]) + "); its title must start with '[rules]' so the change is reviewed as one"]
    return []


def check_pr_description(branch: str, body: str) -> list[str]:
    m = BRANCH_RE.match(branch)
    if not m:
        return []
    errs = []
    if not re.search(rf"(?im)^\s*task\s*:\s*T-{m.group(1)}\b", body or ""):
        errs.append(f"PR description must contain the line 'Task: T-{m.group(1)}'")
    if not re.search(r"(?im)^\s*checked\s*:\s*\S+", body or ""):
        errs.append("PR description must contain a line 'Checked: <how the work was verified>'")
    return errs


def main() -> int:
    base = os.environ.get("BASE_REF", "origin/main")
    branch = os.environ.get("PR_BRANCH") or git("rev-parse", "--abbrev-ref", "HEAD").strip()
    title = os.environ.get("PR_TITLE", "")
    body = os.environ.get("PR_BODY", "")
    is_pr = os.environ.get("IS_PR", "true").lower() == "true"

    files = tracked_files()
    results: list[tuple[str, list[str]]] = [
        ("required docs exist", check_required_docs(files)),
        ("no data, model, secret or oversized files", check_forbidden_files(files)),
        ("no secrets in file contents", check_secrets(files)),
        ("import boundaries between modules", check_import_boundaries(files)),
    ]
    if is_pr:
        changes = changed_files(base)
        results += [
            ("branch name", check_branch_name(branch)),
            ("task file updated, one task per PR", check_task_file(branch, changes)),
            ("docs updated with code", check_docs_with_code(changes)),
            ("tests updated with code", check_tests_with_code(changes, body)),
            ("rule changes are labelled", check_rules_change(changes, title)),
            ("PR description", check_pr_description(branch, body)),
        ]
    failed = 0
    for name, errs in results:
        print(("FAIL  " if errs else "ok    ") + name)
        for e in errs:
            print("        - " + e)
        failed += bool(errs)
    print(f"\n{len(results) - failed} of {len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
