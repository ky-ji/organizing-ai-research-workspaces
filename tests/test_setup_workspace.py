import importlib.util
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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
            canonical_root = root.expanduser().resolve()
            canonical_env_file = env_file.expanduser().resolve()
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
            self.assertIn(
                f"CREATE {canonical_root / 'projects'}", result.stdout
            )
            self.assertIn(f"WRITE {canonical_env_file}", result.stdout)
            self.assertFalse(root.exists())
            self.assertFalse(env_file.exists())
            self.assertFalse(env_file.parent.exists())

    def test_normal_setup_creates_exact_layout_and_exports(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_path = Path(temporary_directory)
            root = temporary_path / "research"
            env_file = temporary_path / "config" / "env.sh"
            canonical_root = root.expanduser().resolve()

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
                ("RESEARCH_ROOT", canonical_root),
                ("PROJECTS_ROOT", canonical_root / "projects"),
                ("SHARED_ROOT", canonical_root / "shared"),
                (
                    "DATASETS_ROOT",
                    canonical_root / "shared" / "datasets",
                ),
                (
                    "PRETRAINED_ROOT",
                    canonical_root / "shared" / "pretrained",
                ),
                ("RUNS_ROOT", canonical_root / "runs"),
                ("SCRATCH_ROOT", canonical_root / "scratch"),
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
            canonical_root = root.expanduser().resolve()
            env_file.write_text("STALE_ENV_CONTENT\n", encoding="utf-8")
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
            expected_env_contents = "".join(
                f"export {name}={shlex.quote(str(value))}\n"
                for name, value in (
                    ("RESEARCH_ROOT", canonical_root),
                    ("PROJECTS_ROOT", canonical_root / "projects"),
                    ("SHARED_ROOT", canonical_root / "shared"),
                    (
                        "DATASETS_ROOT",
                        canonical_root / "shared" / "datasets",
                    ),
                    (
                        "PRETRAINED_ROOT",
                        canonical_root / "shared" / "pretrained",
                    ),
                    ("RUNS_ROOT", canonical_root / "runs"),
                    ("SCRATCH_ROOT", canonical_root / "scratch"),
                )
            ).encode("utf-8")
            self.assertEqual(first_env_contents, expected_env_contents)
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
        with self.subTest("required directory is a file"):
            with tempfile.TemporaryDirectory() as temporary_directory:
                temporary_path = Path(temporary_directory)
                root = temporary_path / "research"
                env_file = temporary_path / "research.env"
                root.mkdir()
                runs_file = root / "runs"
                original_runs_contents = b"occupied\n"
                runs_file.write_bytes(original_runs_contents)

                result = self._run("--root", root, "--env-file", env_file)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("required directory is a file", result.stderr)
                self.assertEqual(set(root.iterdir()), {runs_file})
                self.assertEqual(
                    runs_file.read_bytes(), original_runs_contents
                )
                self.assertFalse(env_file.exists())

        with self.subTest("output aliases required directory"):
            with tempfile.TemporaryDirectory() as temporary_directory:
                temporary_path = Path(temporary_directory)
                real_root = temporary_path / "real-research"
                alias_root = temporary_path / "research-alias"
                real_root.mkdir()
                alias_root.symlink_to(real_root, target_is_directory=True)
                env_file = real_root / "projects"

                result = self._run(
                    "--root", alias_root, "--env-file", env_file
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(list(real_root.iterdir()), [])

        with self.subTest("managed outputs share an inode"):
            with tempfile.TemporaryDirectory() as temporary_directory:
                temporary_path = Path(temporary_directory)
                root = temporary_path / "research"
                env_file = temporary_path / "research.env"
                shell_rc = temporary_path / ".bashrc"
                sentinel = b"do not replace\n"
                env_file.write_bytes(sentinel)
                os.link(env_file, shell_rc)

                result = self._run(
                    "--root",
                    root,
                    "--env-file",
                    env_file,
                    "--shell-rc",
                    shell_rc,
                )

                with self.subTest(check="nonzero exit"):
                    self.assertNotEqual(result.returncode, 0)
                with self.subTest(check="env sentinel unchanged"):
                    self.assertEqual(env_file.read_bytes(), sentinel)
                with self.subTest(check="shell sentinel unchanged"):
                    self.assertEqual(shell_rc.read_bytes(), sentinel)
                with self.subTest(check="workspace absent"):
                    self.assertFalse(root.exists())

        with self.subTest("nested output aliases required directory"):
            with tempfile.TemporaryDirectory() as temporary_directory:
                temporary_path = Path(temporary_directory)
                root = temporary_path / "research"
                external_shared = temporary_path / "external-shared"
                root.mkdir()
                external_shared.mkdir()
                shared_link = root / "shared"
                shared_link.symlink_to(
                    external_shared, target_is_directory=True
                )
                env_file = external_shared / "datasets"

                result = self._run(
                    "--root", root, "--env-file", env_file
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(set(root.iterdir()), {shared_link})
                self.assertTrue(shared_link.is_symlink())
                self.assertEqual(list(external_shared.iterdir()), [])

    def test_setup_without_shell_rc_leaves_bashrc_unchanged(self):
        with self.subTest("shell rc is opt in"):
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

        with self.subTest("atomic write keeps old target on replace failure"):
            spec = importlib.util.spec_from_file_location(
                "setup_workspace_under_test", SCRIPT
            )
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertTrue(
                hasattr(module, "_atomic_write_text"),
                "atomic write helper is missing",
            )
            atomic_write = module._atomic_write_text

            with tempfile.TemporaryDirectory() as temporary_directory:
                temporary_path = Path(temporary_directory)
                target = temporary_path / "managed.env"
                old_bytes = b"old managed content\n"
                target.write_bytes(old_bytes)

                with mock.patch.object(
                    module.os,
                    "replace",
                    side_effect=OSError("injected replace failure"),
                ):
                    with self.assertRaises(OSError):
                        atomic_write(target, "new managed content\n")

                self.assertEqual(target.read_bytes(), old_bytes)
                self.assertEqual(set(temporary_path.iterdir()), {target})


if __name__ == "__main__":
    unittest.main()
