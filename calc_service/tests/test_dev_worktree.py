"""scripts/dev.py: управление worktree для параллельных задач (wt-add / wt-rm)."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("dev_cli", ROOT / "scripts" / "dev.py")
dev_cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dev_cli)


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", *args],
        cwd=cwd,
        text=True,
        encoding="utf-8",
    ).strip()


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "insain-agent"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "init")
    return repo


def test_wt_add_requires_committed_todo(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    (repo / "todo").mkdir()
    (repo / "todo" / "demo.md").write_text("# demo\nСтатус: черновик\n", encoding="utf-8")
    monkeypatch.setattr(dev_cli, "ROOT", repo)

    with pytest.raises(SystemExit, match="не закоммичен"):
        dev_cli.cmd_wt_add("demo")


def test_wt_add_requires_main_branch(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    _git(repo, "switch", "-c", "feature")
    monkeypatch.setattr(dev_cli, "ROOT", repo)

    with pytest.raises(SystemExit, match="ветке main"):
        dev_cli.cmd_wt_add("demo")


def test_wt_add_and_wt_rm_roundtrip(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    (repo / "todo").mkdir()
    (repo / "todo" / "demo.md").write_text("# demo\nСтатус: черновик\n", encoding="utf-8")
    _git(repo, "add", "todo/demo.md")
    _git(repo, "commit", "-m", "Add todo demo")
    monkeypatch.setattr(dev_cli, "ROOT", repo)

    wt = dev_cli.cmd_wt_add("todo/demo.md")
    assert wt == tmp_path / "insain-agent-demo"
    assert wt.is_dir()
    assert _git(wt, "branch", "--show-current") == "task/demo"

    (wt / "work.txt").write_text("ok\n", encoding="utf-8")
    _git(wt, "add", "work.txt")
    _git(wt, "commit", "-m", "Work on demo")
    _git(repo, "merge", "--ff-only", "task/demo")

    dev_cli.cmd_wt_rm("demo")
    assert not wt.exists()
    assert "task/demo" not in _git(repo, "branch", "--list", "task/demo")


def test_wt_rm_refuses_dirty_worktree(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    (repo / "todo").mkdir()
    (repo / "todo" / "demo.md").write_text("# demo\nСтатус: черновик\n", encoding="utf-8")
    _git(repo, "add", "todo/demo.md")
    _git(repo, "commit", "-m", "Add todo demo")
    monkeypatch.setattr(dev_cli, "ROOT", repo)

    wt = dev_cli.cmd_wt_add("demo")
    (wt / "dirty.txt").write_text("untracked\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        dev_cli.cmd_wt_rm("demo")
    assert wt.is_dir()

    (wt / "dirty.txt").unlink()
    dev_cli.cmd_wt_rm("demo")


def test_wt_add_idempotent_when_already_exists(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    (repo / "todo").mkdir()
    (repo / "todo" / "demo.md").write_text("# demo\nСтатус: черновик\n", encoding="utf-8")
    _git(repo, "add", "todo/demo.md")
    _git(repo, "commit", "-m", "Add todo demo")
    monkeypatch.setattr(dev_cli, "ROOT", repo)

    wt1 = dev_cli.cmd_wt_add("demo")
    wt2 = dev_cli.cmd_wt_add("demo")
    assert wt1 == wt2
    dev_cli.cmd_wt_rm("demo")


def test_wt_add_checks_file_conflicts_against_active_tasks(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    (repo / "todo").mkdir()
    (repo / "todo" / "task-a.md").write_text(
        "# task-a\nСтатус: в работе\n\n## Файлы\n\n- `calc_service/calculators/laser.py`\n",
        encoding="utf-8",
    )
    (repo / "todo" / "task-b.md").write_text(
        "# task-b\nСтатус: черновик\n\n## Файлы\n\n- `calc_service/calculators/laser.py`\n",
        encoding="utf-8",
    )
    (repo / "todo" / "task-c.md").write_text(
        "# task-c\nСтатус: черновик\n\n## Файлы\n\n- `calc_service/calculators/sticker.py`\n",
        encoding="utf-8",
    )
    _git(repo, "add", "todo")
    _git(repo, "commit", "-m", "Add tasks")
    monkeypatch.setattr(dev_cli, "ROOT", repo)

    with pytest.raises(SystemExit, match="пересечение"):
        dev_cli.cmd_wt_add("task-b")

    wt_c = dev_cli.cmd_wt_add("task-c")
    assert wt_c.is_dir()
    wt_b_forced = dev_cli.cmd_wt_add("task-b", force=True)
    assert wt_b_forced.is_dir()

    dev_cli.cmd_wt_rm("task-c")
    dev_cli.cmd_wt_rm("task-b")


def test_wt_check_detects_dirty_main_from_worktree(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    (repo / "todo").mkdir()
    (repo / "todo" / "demo.md").write_text("# demo\nСтатус: черновик\n", encoding="utf-8")
    _git(repo, "add", "todo/demo.md")
    _git(repo, "commit", "-m", "Add todo demo")
    monkeypatch.setattr(dev_cli, "ROOT", repo)

    wt = dev_cli.cmd_wt_add("demo")
    monkeypatch.setattr(dev_cli, "ROOT", wt)
    dev_cli.cmd_wt_check("demo")

    (repo / "accidental.txt").write_text("oops\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="незакоммиченные правки"):
        dev_cli.cmd_wt_check("demo")

    (repo / "accidental.txt").unlink()
    dev_cli.cmd_wt_check("demo")
    monkeypatch.setattr(dev_cli, "ROOT", repo)
    dev_cli.cmd_wt_rm("demo")


def test_lock_acquire_release_shared_across_worktrees(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    (repo / "todo").mkdir()
    (repo / "todo" / "t1.md").write_text("# t1\nСтатус: черновик\n", encoding="utf-8")
    _git(repo, "add", "todo/t1.md")
    _git(repo, "commit", "-m", "Add t1")
    monkeypatch.setattr(dev_cli, "ROOT", repo)

    wt = dev_cli.cmd_wt_add("t1")

    dev_cli.cmd_lock_acquire("prod", "t1")
    dev_cli.cmd_lock_acquire("prod", "t1")

    monkeypatch.setattr(dev_cli, "ROOT", wt)
    with pytest.raises(SystemExit, match="занят задачей 't1'"):
        dev_cli.cmd_lock_acquire("prod", "t2")
    with pytest.raises(SystemExit, match="удерживает задача 't1'"):
        dev_cli.cmd_lock_release("prod", "t2")

    dev_cli.cmd_lock_release("prod", "t1")
    dev_cli.cmd_lock_acquire("merge", "t2")
    dev_cli.cmd_lock_release("merge", "other", force=True)

    monkeypatch.setattr(dev_cli, "ROOT", repo)
    dev_cli.cmd_wt_rm("t1")
