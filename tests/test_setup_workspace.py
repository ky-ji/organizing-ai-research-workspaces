import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "organizing-ai-research-workspaces"
SCRIPT = SKILL_ROOT / "scripts" / "setup_workspace.py"


class SetupWorkspaceTests(unittest.TestCase):
    def _run(self, *arguments, env=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, arguments)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_dry_run_reports_changes_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            home = temporary_path / "home"
            home.mkdir()
            root = home / "research"
            env_file = home / "config" / "env.sh"
            process_env = os.environ.copy()
            process_env["HOME"] = str(home)

            result = self._run(
                "--root",
                "~/research",
                "--env-file",
                "~/config/env.sh",
                "--dry-run",
                env=process_env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"CREATE {root / 'projects'}", result.stdout)
            self.assertIn(f"WRITE {env_file}", result.stdout)
            self.assertFalse(root.exists())
            self.assertFalse(env_file.exists())
            self.assertFalse(env_file.parent.exists())

    def test_normal_setup_creates_exact_layout_and_exports(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            root = temporary_path / "research"
            env_file = temporary_path / "config" / "env.sh"

            result = self._run("--root", root, "--env-file", env_file)

            self.assertEqual(result.returncode, 0, result.stderr)
            expected_directories = {
                "projects",
                "shared",
                "shared/datasets",
                "shared/pretrained",
                "runs",
                "scratch",
            }
            actual_paths = list(root.rglob("*"))
            self.assertEqual(
                {path.relative_to(root).as_posix() for path in actual_paths},
                expected_directories,
            )
            self.assertTrue(all(path.is_dir() for path in actual_paths))

            env_contents = env_file.read_text(encoding="utf-8")
            self.assertTrue(env_contents.endswith("\n"))
            env_lines = env_contents.splitlines()
            expected_exports = [
                ("RESEARCH_ROOT", root),
                ("PROJECTS_ROOT", root / "projects"),
                ("SHARED_ROOT", root / "shared"),
                ("DATASETS_ROOT", root / "shared" / "datasets"),
                ("PRETRAINED_ROOT", root / "shared" / "pretrained"),
                ("RUNS_ROOT", root / "runs"),
                ("SCRATCH_ROOT", root / "scratch"),
            ]
            self.assertEqual(len(env_lines), 7)
            for line, (name, value) in zip(env_lines, expected_exports):
                prefix = f"export {name}="
                self.assertTrue(line.startswith(prefix), line)
                self.assertEqual(shlex.split(line.removeprefix(prefix)), [str(value)])

    def test_repeated_setup_preserves_content_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            root = temporary_path / "research"
            env_file = temporary_path / "research.env"
            shell_rc = temporary_path / ".bashrc"
            original_rc = "# existing shell content\nexport PATH=\"$HOME/bin:$PATH\"\n"
            shell_rc.write_text(original_rc, encoding="utf-8")

            first_result = self._run(
                "--root",
                root,
                "--env-file",
                env_file,
                "--shell-rc",
                shell_rc,
            )

            self.assertEqual(first_result.returncode, 0, first_result.stderr)
            first_env_contents = env_file.read_bytes()
            first_rc_contents = shell_rc.read_bytes()
            self.assertIn(original_rc.encode("utf-8"), first_rc_contents)
            self.assertEqual(
                first_rc_contents.count(b"# >>> research-workspace >>>"),
                1,
            )

            second_result = self._run(
                "--root",
                root,
                "--env-file",
                env_file,
                "--shell-rc",
                shell_rc,
            )

            self.assertEqual(second_result.returncode, 0, second_result.stderr)
            self.assertEqual(env_file.read_bytes(), first_env_contents)
            self.assertEqual(shell_rc.read_bytes(), first_rc_contents)
            for action in ("CREATE", "WRITE", "UPDATE"):
                self.assertNotIn(action, second_result.stdout)

    def test_file_collision_fails_before_creating_directories(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            root = temporary_path / "research"
            env_file = temporary_path / "research.env"
            root.mkdir()
            runs_file = root / "runs"
            runs_file.write_text("occupied\n", encoding="utf-8")

            result = self._run("--root", root, "--env-file", env_file)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("required directory is a file", result.stderr)
            self.assertEqual(set(root.iterdir()), {runs_file})
            self.assertFalse(env_file.exists())

    def test_setup_without_shell_rc_leaves_bashrc_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            home = temporary_path / "home"
            home.mkdir()
            bashrc = home / ".bashrc"
            original_bashrc = "# leave this file alone\n"
            bashrc.write_text(original_bashrc, encoding="utf-8")
            root = temporary_path / "research"
            env_file = temporary_path / "research.env"
            process_env = os.environ.copy()
            process_env["HOME"] = str(home)

            result = self._run(
                "--root",
                root,
                "--env-file",
                env_file,
                env=process_env,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                bashrc.read_text(encoding="utf-8"), original_bashrc
            )


if __name__ == "__main__":
    unittest.main()
