import subprocess
import tempfile
from pathlib import Path
from workbench.companion import capture_git_diff, command
from workbench.store import put, get


def test_capture_git_diff_in_git_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

        # Initial commit
        initial_file = repo_path / "hello.txt"
        initial_file.write_text("initial content\n")
        subprocess.run(["git", "add", "hello.txt"], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "initial commit"], cwd=repo_path, check=True)

        # Before any modification, git status is clean -> returns None
        assert capture_git_diff(repo_path) is None

        # Modify a file and add an untracked file
        initial_file.write_text("initial content\nnew modified line\n")
        new_file = repo_path / "second.txt"
        new_file.write_text("second file\n")

        diff_info = capture_git_diff(repo_path)
        assert diff_info is not None
        assert "+new modified line" in diff_info["diff"]
        assert "hello.txt" in diff_info["modified_files"]
        assert "second.txt" in diff_info["modified_files"]


def test_capture_git_diff_non_git_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        res = capture_git_diff(Path(tmpdir))
        assert res is None


def test_companion_command_captures_shell_git_diff():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

        f = repo_path / "file.txt"
        f.write_text("line 1\n")
        subprocess.run(["git", "add", "file.txt"], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo_path, check=True)

        run_id = "test-shell-diff-run"
        grant_id = "test-shell-diff-grant"
        put("grants", {"id": grant_id, "mode": "host", "root": str(repo_path), "capabilities": ["shell"], "revoked": False})
        put("runs", {"id": run_id, "grant": grant_id, "mode": "host", "status": "running", "tools": ["shell"]})

        action = {"op": "shell", "command": "echo 'line 2' >> file.txt"}
        res = command(get("runs", run_id), ["bash", "-lc", action["command"]], repo_path, action)

        assert res["exit_status"] == 0
        assert "diff" in res
        assert "+line 2" in res["diff"]
        assert "file.txt" in res["modified_files"]
