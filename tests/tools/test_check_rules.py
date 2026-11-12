import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("check_rules", Path(__file__).resolve().parents[2] / "tools" / "check_rules.py")
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)


def test_branch_name():
    assert cr.check_branch_name("task/T-002-survivor-free-data") == []
    assert cr.check_branch_name("main")
    assert cr.check_branch_name("feature/x")
    assert cr.check_branch_name("task/T-2-x")
    assert cr.check_branch_name("task/T-002-Has_Caps")


def test_task_file_required_and_single():
    b = "task/T-002-data"
    assert cr.check_task_file(b, [("M", "docs/tasks/T-002-survivor-free-data.md")]) == []
    assert cr.check_task_file(b, [("M", "common/data/x.py")])
    # adding new task files is allowed (manager creating tasks); modifying another task's file is not
    assert cr.check_task_file(b, [("M", "docs/tasks/T-002-a.md"), ("A", "docs/tasks/T-009-new.md")]) == []
    assert cr.check_task_file(b, [("M", "docs/tasks/T-002-a.md"), ("M", "docs/tasks/T-003-b.md")])


def test_docs_with_code():
    assert cr.check_docs_with_code([("M", "common/data/x.py")])
    assert cr.check_docs_with_code([("M", "common/data/x.py"), ("M", "docs/PLAN.md")]) == []
    assert cr.check_docs_with_code([("M", "research/a.py")]) == []


def test_tests_with_code():
    code = [("A", "common/signals/momentum.py")]
    assert cr.check_tests_with_code(code, "")
    assert cr.check_tests_with_code(code + [("A", "tests/common/signals/test_momentum.py")], "") == []
    assert cr.check_tests_with_code(code, "Task: T-004\nNo-test-reason: pure rename") == []
    assert cr.check_tests_with_code([("A", "common/signals/__init__.py")], "") == []


def test_rules_change_needs_label():
    ch = [("M", "CLAUDE.md")]
    assert cr.check_rules_change(ch, "Add loader")
    assert cr.check_rules_change(ch, "[rules] Tighten git rules") == []
    assert cr.check_rules_change([("M", ".github/workflows/checks.yml")], "x")
    assert cr.check_rules_change([("M", "docs/PLAN.md")], "x") == []


def test_pr_description():
    b = "task/T-002-data"
    assert cr.check_pr_description(b, "Task: T-002\nChecked: ran pytest") == []
    assert len(cr.check_pr_description(b, "")) == 2
    assert cr.check_pr_description(b, "Task: T-003\nChecked: yes")


def test_import_boundaries():
    v = cr.import_violation
    assert v(("common",), "markets.india.adapters.nse")
    assert v(("common",), "common.signals.momentum") is None
    assert v(("markets", "india", "swing"), "markets.us.adapters.x")
    assert v(("markets", "india", "swing"), "markets.india.positional.engine")
    assert v(("markets", "india", "swing"), "markets.india.adapters.nse") is None
    assert v(("markets", "india", "swing"), "common.priceaction.candles") is None
    assert v(("markets", "india", "adapters"), "markets.india.swing.rules")
    assert v(("services",), "research.sim")
    assert v(("services",), "markets.india.positional.engine") is None
    assert v(("research",), "research.helpers") is None


def test_secret_patterns():
    p = cr.SECRET_PATTERNS
    assert p["Telegram bot token"].search("token 123456789:" + "A" * 35)
    assert p["assigned secret"].search('API_KEY = "' + "a1B2" * 6 + '"')
    assert not p["assigned secret"].search('api_key = os.environ["BROKER_API_KEY"]')
    assert p["AWS access key"].search("AKIA" + "A" * 16)
