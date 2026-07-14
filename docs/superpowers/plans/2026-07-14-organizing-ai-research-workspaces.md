# Organizing AI Research Workspaces Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Build, publish, install, and apply a tested agent skill that creates a minimal four-root AI research workspace and safely configures it on volcengine3.

**Architecture:** Keep the installable skill under skills/organizing-ai-research-workspaces/, tests under tests/, and design material under docs/superpowers/. A standard-library Python CLI performs deterministic, idempotent setup; SKILL.md supplies the judgment layer for storage inspection, Git boundaries, cross-machine paths, and checkpoint placement.

**Tech Stack:** Markdown agent skill, Python 3 standard library, unittest, Git, GitHub CLI, SSH.

---

## File map

- skills/organizing-ai-research-workspaces/SKILL.md: concise method and trigger metadata.
- skills/organizing-ai-research-workspaces/agents/openai.yaml: Codex UI metadata.
- skills/organizing-ai-research-workspaces/scripts/setup_workspace.py: idempotent setup CLI.
- tests/test_setup_workspace.py: CLI behavior tests.
- tests/test_skill_contract.py: skill structure and content contract.
- docs/superpowers/specs/2026-07-14-organizing-ai-research-workspaces-design.md: approved design.
- docs/superpowers/plans/2026-07-14-organizing-ai-research-workspaces.md: this plan.

### Task 1: Establish RED tests

**Files:**
- Create: tests/test_setup_workspace.py
- Create: tests/test_skill_contract.py

- [ ] **Step 1: Write tests/test_setup_workspace.py before the CLI exists**

~~~python
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "organizing-ai-research-workspaces"
SCRIPT = SKILL_ROOT / "scripts" / "setup_workspace.py"


class SetupWorkspaceTests(unittest.TestCase):
    def run_setup(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_dry_run_reports_plan_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "research"
            env_file = base / "env.sh"
            result = self.run_setup(
                "--root", str(root), "--env-file", str(env_file), "--dry-run"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"CREATE {root / 'projects'}", result.stdout)
            self.assertIn(f"WRITE {env_file}", result.stdout)
            self.assertFalse(root.exists())
            self.assertFalse(env_file.exists())

    def test_creates_exact_workspace_and_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "research"
            env_file = base / "config" / "env.sh"
            result = self.run_setup("--root", str(root), "--env-file", str(env_file))
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = {
                root / "projects",
                root / "shared",
                root / "shared" / "datasets",
                root / "shared" / "pretrained",
                root / "runs",
                root / "scratch",
            }
            self.assertEqual({p for p in root.rglob("*") if p.is_dir()}, expected)
            self.assertEqual(
                env_file.read_text(),
                "\n".join(
                    [
                        f"export RESEARCH_ROOT={root}",
                        f"export PROJECTS_ROOT={root / 'projects'}",
                        f"export SHARED_ROOT={root / 'shared'}",
                        f"export DATASETS_ROOT={root / 'shared' / 'datasets'}",
                        f"export PRETRAINED_ROOT={root / 'shared' / 'pretrained'}",
                        f"export RUNS_ROOT={root / 'runs'}",
                        f"export SCRATCH_ROOT={root / 'scratch'}",
                        "",
                    ]
                ),
            )

    def test_repeated_setup_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "research"
            env_file = base / "env.sh"
            shell_rc = base / ".bashrc"
            shell_rc.write_text("export EXISTING=1\n")
            args = (
                "--root", str(root),
                "--env-file", str(env_file),
                "--shell-rc", str(shell_rc),
            )
            first = self.run_setup(*args)
            first_env = env_file.read_text()
            first_rc = shell_rc.read_text()
            second = self.run_setup(*args)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(env_file.read_text(), first_env)
            self.assertEqual(shell_rc.read_text(), first_rc)
            self.assertEqual(first_rc.count("# >>> research-workspace >>>"), 1)
            self.assertIn("export EXISTING=1", first_rc)
            self.assertNotIn("CREATE ", second.stdout)
            self.assertNotIn("WRITE ", second.stdout)
            self.assertNotIn("UPDATE ", second.stdout)

    def test_refuses_required_path_occupied_by_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "research"
            root.mkdir()
            (root / "runs").write_text("conflict")
            result = self.run_setup(
                "--root", str(root), "--env-file", str(base / "env.sh")
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("required directory is a file", result.stderr)
            self.assertFalse((root / "projects").exists())

    def test_shell_rc_is_untouched_without_explicit_option(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "research"
            shell_rc = base / ".bashrc"
            shell_rc.write_text("export EXISTING=1\n")
            result = self.run_setup(
                "--root", str(root), "--env-file", str(base / "env.sh")
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(shell_rc.read_text(), "export EXISTING=1\n")


if __name__ == "__main__":
    unittest.main()
~~~

- [ ] **Step 2: Write tests/test_skill_contract.py before the skill exists**

~~~python
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "organizing-ai-research-workspaces"


class SkillContractTests(unittest.TestCase):
    def test_skill_frontmatter_and_trigger_contract(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text()
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match)
        frontmatter = match.group(1).splitlines()
        self.assertEqual(frontmatter[0], "name: organizing-ai-research-workspaces")
        self.assertEqual(len(frontmatter), 2)
        self.assertTrue(frontmatter[1].startswith("description: Use when "))
        self.assertLessEqual(len(match.group(1)), 1024)

    def test_methodology_keeps_the_exact_four_root_contract(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text()
        contract = text.split("<!-- contract:start -->", 1)[1].split(
            "<!-- contract:end -->", 1
        )[0]
        for required in (
            "projects/",
            "shared/",
            "datasets/",
            "pretrained/",
            "runs/",
            "scratch/",
        ):
            self.assertIn(required, contract)
        for forbidden in ("archived/", "artifacts/", "models/"):
            self.assertNotIn(forbidden, contract)

    def test_checkpoint_and_cross_machine_rules_are_explicit(self) -> None:
        text = (SKILL_ROOT / "SKILL.md").read_text()
        for required in (
            "runs/<project>/<run-id>/checkpoints/",
            "paper-runs.yaml",
            "KEEP",
            "RESEARCH_ROOT",
            "DATASETS_ROOT",
            "PRETRAINED_ROOT",
            "RUNS_ROOT",
            "world-writable",
            "sticky bit",
        ):
            self.assertIn(required, text)
        self.assertLessEqual(len(text.split()), 800)

    def test_openai_metadata_invokes_the_skill_by_name(self) -> None:
        text = (SKILL_ROOT / "agents" / "openai.yaml").read_text()
        self.assertIn('display_name: "Organizing AI Research Workspaces"', text)
        self.assertIn("$organizing-ai-research-workspaces", text)


if __name__ == "__main__":
    unittest.main()
~~~

- [ ] **Step 3: Run both test modules and verify RED**

Run:

~~~bash
python3 -m unittest tests.test_setup_workspace tests.test_skill_contract -v
~~~

Expected: nine errors/failures caused by absent skill files. Syntax or test-discovery errors are not an acceptable RED result.

- [ ] **Step 4: Commit the RED tests**

~~~bash
git add tests/test_setup_workspace.py tests/test_skill_contract.py
git commit -m "test: define research workspace skill behavior"
~~~

### Task 2: Initialize the official skill skeleton

**Files:**
- Create: skills/organizing-ai-research-workspaces/SKILL.md
- Create: skills/organizing-ai-research-workspaces/agents/openai.yaml
- Create: skills/organizing-ai-research-workspaces/scripts/

- [ ] **Step 1: Run the official initializer**

~~~bash
python3 /Users/jky/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  organizing-ai-research-workspaces \
  --path skills \
  --resources scripts \
  --interface 'display_name=Organizing AI Research Workspaces' \
  --interface 'short_description=Simple, traceable AI research storage' \
  --interface 'default_prompt=Use $organizing-ai-research-workspaces to set up a simple, traceable research directory across my machines.'
~~~

Expected: the skeleton and agents/openai.yaml are created with no example resource files.

- [ ] **Step 2: Re-run the tests**

~~~bash
python3 -m unittest tests.test_setup_workspace tests.test_skill_contract -v
~~~

Expected: tests remain RED because the skeleton does not implement the approved contract.

### Task 3: Implement the setup CLI

**Files:**
- Create: skills/organizing-ai-research-workspaces/scripts/setup_workspace.py

- [ ] **Step 1: Add the minimal tested implementation**

~~~python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shlex
import sys
from pathlib import Path


MANAGED_START = "# >>> research-workspace >>>"
MANAGED_END = "# <<< research-workspace <<<"


class WorkspaceError(Exception):
    pass


def resolve_path(raw: str) -> Path:
    return Path(raw).expanduser().resolve()


def required_directories(root: Path) -> list[Path]:
    return [
        root,
        root / "projects",
        root / "shared",
        root / "shared" / "datasets",
        root / "shared" / "pretrained",
        root / "runs",
        root / "scratch",
    ]


def environment_text(root: Path) -> str:
    values = {
        "RESEARCH_ROOT": root,
        "PROJECTS_ROOT": root / "projects",
        "SHARED_ROOT": root / "shared",
        "DATASETS_ROOT": root / "shared" / "datasets",
        "PRETRAINED_ROOT": root / "shared" / "pretrained",
        "RUNS_ROOT": root / "runs",
        "SCRATCH_ROOT": root / "scratch",
    }
    return "".join(
        f"export {name}={shlex.quote(str(path))}\n"
        for name, path in values.items()
    )


def managed_shell_text(current: str, env_file: Path) -> str:
    quoted = shlex.quote(str(env_file))
    block = (
        f"{MANAGED_START}\n"
        f"[ -f {quoted} ] && . {quoted}\n"
        f"{MANAGED_END}"
    )
    has_start = MANAGED_START in current
    has_end = MANAGED_END in current
    if has_start != has_end:
        raise WorkspaceError("shell rc contains an incomplete research-workspace block")
    if has_start:
        pattern = re.compile(
            re.escape(MANAGED_START) + r".*?" + re.escape(MANAGED_END),
            re.DOTALL,
        )
        return pattern.sub(block, current)
    prefix = current
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    if prefix:
        prefix += "\n"
    return prefix + block + "\n"


def preflight(
    directories: list[Path], env_file: Path, shell_rc: Path | None
) -> None:
    for path in directories:
        if path.exists() and not path.is_dir():
            raise WorkspaceError(f"required directory is a file: {path}")
    if env_file.exists() and not env_file.is_file():
        raise WorkspaceError(f"environment file path is not a file: {env_file}")
    if shell_rc is not None and shell_rc.exists() and not shell_rc.is_file():
        raise WorkspaceError(f"shell rc path is not a file: {shell_rc}")


def ensure_directory(path: Path, dry_run: bool) -> None:
    if path.is_dir():
        print(f"UNCHANGED {path}")
        return
    print(f"CREATE {path}")
    if not dry_run:
        path.mkdir(parents=True, exist_ok=True)


def write_if_changed(
    path: Path, content: str, dry_run: bool, action: str
) -> None:
    if path.exists() and path.read_text() == content:
        print(f"UNCHANGED {path}")
        return
    print(f"{action} {path}")
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a minimal AI research workspace."
    )
    parser.add_argument("--root", required=True)
    parser.add_argument(
        "--env-file",
        default=str(Path.home() / ".config" / "research-workspace" / "env.sh"),
    )
    parser.add_argument("--shell-rc")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = resolve_path(args.root)
    env_file = resolve_path(args.env_file)
    shell_rc = resolve_path(args.shell_rc) if args.shell_rc else None
    directories = required_directories(root)
    try:
        preflight(directories, env_file, shell_rc)
        for directory in directories:
            ensure_directory(directory, args.dry_run)
        write_if_changed(
            env_file, environment_text(root), args.dry_run, "WRITE"
        )
        if shell_rc is not None:
            current = shell_rc.read_text() if shell_rc.exists() else ""
            updated = managed_shell_text(current, env_file)
            write_if_changed(shell_rc, updated, args.dry_run, "UPDATE")
    except (OSError, WorkspaceError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
~~~

- [ ] **Step 2: Run setup tests and verify GREEN**

~~~bash
python3 -m unittest tests.test_setup_workspace -v
~~~

Expected: 5 tests pass, 0 failures.

- [ ] **Step 3: Commit the setup CLI**

~~~bash
git add skills/organizing-ai-research-workspaces/scripts/setup_workspace.py
git commit -m "feat: add idempotent research workspace setup"
~~~

### Task 4: Write the minimal methodology skill

**Files:**
- Modify: skills/organizing-ai-research-workspaces/SKILL.md
- Verify: skills/organizing-ai-research-workspaces/agents/openai.yaml

- [ ] **Step 1: Replace the skeleton with this complete SKILL.md**

~~~~markdown
---
name: organizing-ai-research-workspaces
description: Use when setting up, auditing, or simplifying AI/ML research storage across laptops, GitHub, GPU servers, or clusters, especially when projects share datasets and pretrained weights or produce many runs and checkpoints.
---

# Organizing AI Research Workspaces

## Overview

Keep the logical structure small and make every paper result traceable by reference. Separate Git projects, shared inputs, run outputs, and disposable scratch data without adding lifecycle hierarchies.

## Workflow

1. Inspect before mutating: identify the user, mounts, filesystems, free space, ownership, mode, ACLs, bind mounts, symlinks, and actual write access.
2. Choose the safest currently writable root with adequate capacity. Treat root-owned empty disks as unavailable until a user-owned directory exists.
3. Present the mapping and any tradeoffs. Require confirmation before destructive cleanup or changing shared permissions.
4. Create the contract with scripts/setup_workspace.py.
5. Verify structure, environment variables, filesystem identity, ownership, and a second idempotent run.

## Directory Contract

<!-- contract:start -->
~~~text
research/
├── projects/
├── shared/
│   ├── datasets/
│   └── pretrained/
├── runs/
└── scratch/
~~~
<!-- contract:end -->

Do not add active, submitted, published, deprecated, or archived project layers. Each potential paper is one Git repository directly under projects/. Add tests/ or notebooks/ inside a project only when needed.

## Runs and Checkpoints

Use runs/<project>/<run-id>/ with run IDs shaped as YYYYMMDD-HHMM_<git-sha7>_<purpose>. Keep resolved configuration, metadata, metrics, logs, and runs/<project>/<run-id>/checkpoints/ together.

Retain last plus the best one or few checkpoints. A paper-selected model stays in its original run. Track only its run ID and checkpoint name in the project repository's results/paper-runs.yaml and add a KEEP marker to that run. Do not create a second paper-model copy by default.

## Git Boundary

| Track in Git | Keep outside Git |
|---|---|
| Code, configs, environment locks, paper source, small results, run references | Datasets, downloaded weights, checkpoints, full logs, caches, secrets |

Never hardcode machine paths in project code. Resolve storage from RESEARCH_ROOT, PROJECTS_ROOT, SHARED_ROOT, DATASETS_ROOT, PRETRAINED_ROOT, RUNS_ROOT, and SCRATCH_ROOT.

## Storage Safety

Reject a world-writable directory without the sticky bit for unique checkpoints: another user may rename or delete entries. Do not assume a mounted disk is usable from capacity alone; check its complete path permissions and ACLs. Prefer a safe home-backed NVMe now over an inaccessible empty disk. Move physical storage later only behind the same logical variables.

Backups, archive trees, DVC, MLflow, W&B, object storage, and model registries are opt-in. Introduce them only when the user explicitly requests their tradeoffs.

## Example

After confirming that home is the safe large filesystem:

~~~bash
python3 scripts/setup_workspace.py \
  --root "$HOME/research" \
  --env-file "$HOME/.config/research-workspace/env.sh" \
  --shell-rc "$HOME/.bashrc"
~~~

Then verify findmnt -T "$RUNS_ROOT", namei -l "$RUNS_ROOT", and run the command again; the second run must report only UNCHANGED actions.

## Quick Reference

| Question | Default |
|---|---|
| Where does code live? | projects/<paper>/ |
| Where are shared inputs? | shared/datasets/ and shared/pretrained/ |
| Where is a checkpoint? | Its originating run |
| How is a paper model retained? | paper-runs.yaml plus KEEP |
| What may be deleted freely? | scratch/ |

## Red Flags and Common Mistakes

Stop if a proposal adds status folders, a model registry, or a backup policy without being asked; writes to a mount root because it looks empty; hardcodes /home or /data paths in project code; commits checkpoints to Git; or calls a setup complete without verifying a second run.
~~~~

- [ ] **Step 2: Run the contract tests and verify GREEN**

~~~bash
python3 -m unittest tests.test_skill_contract -v
~~~

Expected: 4 tests pass, 0 failures.

- [ ] **Step 3: Check generated UI metadata**

~~~bash
sed -n '1,120p' skills/organizing-ai-research-workspaces/agents/openai.yaml
~~~

Expected:

~~~yaml
interface:
  display_name: "Organizing AI Research Workspaces"
  short_description: "Simple, traceable AI research storage"
  default_prompt: "Use $organizing-ai-research-workspaces to set up a simple, traceable research directory across my machines."
~~~

Regenerate with generate_openai_yaml.py and the same three interface values if it differs.

- [ ] **Step 4: Commit the methodology**

~~~bash
git add skills/organizing-ai-research-workspaces/SKILL.md \
  skills/organizing-ai-research-workspaces/agents/openai.yaml
git commit -m "feat: add AI research workspace methodology"
~~~

### Task 5: Validate and forward-test

**Files:**
- Modify skill or tests only if validation exposes a real gap.

- [ ] **Step 1: Run all local tests**

~~~bash
python3 -m unittest discover -s tests -v
~~~

Expected: 9 tests pass, 0 failures.

- [ ] **Step 2: Run the official validator and static checks**

~~~bash
python3 /Users/jky/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/organizing-ai-research-workspaces
git diff --check main...HEAD
rg -n 'TBD|TODO|final-v[0-9]|new-new' skills tests
wc -w skills/organizing-ai-research-workspaces/SKILL.md
~~~

Expected: validation succeeds, no whitespace or placeholder matches, and SKILL.md has at most 800 words.

- [ ] **Step 3: Rerun the three original scenarios with fresh agents and the new skill**

Pass only the skill path and one original request to each agent. Verify that outputs preserve the exact four-root contract, choose currently safe writable storage, and keep checkpoint rules simple. If an agent adds default archive/model-registry layers or selects inaccessible storage, add the narrowest counter and rerun that scenario.

- [ ] **Step 4: Commit only if forward testing requires refinement**

~~~bash
git add skills/organizing-ai-research-workspaces tests
git commit -m "refine: close research workspace workflow gaps"
~~~

Skip this commit when no source file changes.

### Task 6: Publish to GitHub

**Files:**
- No source edits expected.

- [ ] **Step 1: Verify scope and authentication**

~~~bash
git status -sb
git diff --stat main...HEAD
gh auth status
~~~

Expected: only approved skill, tests, and planning files are in scope; account ky-ji is authenticated.

- [ ] **Step 2: Commit this plan on the implementation branch, create a public repository, and push main**

Commit this plan in the current implementation worktree. Then create the repository and push the existing main ref:

~~~bash
gh repo create ky-ji/organizing-ai-research-workspaces \
  --public \
  --description "A minimal, traceable workspace method for AI research projects, shared data, runs, and checkpoints"
git remote add origin https://github.com/ky-ji/organizing-ai-research-workspaces.git
git push -u origin main
~~~

Expected: the public repository exists; main contains the approved design, while the implementation branch contains this plan and the tested skill.

- [ ] **Step 3: Push the implementation branch and open a draft PR**

~~~bash
git push -u origin agent/research-workspace-skill
gh pr create \
  --draft \
  --base main \
  --head agent/research-workspace-skill \
  --title "Add AI research workspace skill" \
  --body-file /tmp/organizing-ai-research-workspaces-pr.md
~~~

The PR body must describe the method, public-skill comparison, RED/GREEN evidence, and remote deployment plan.

### Task 7: Install and apply on volcengine3

**Files:**
- Install locally: /Users/jky/.codex/skills/organizing-ai-research-workspaces
- Create remotely: /home/kangye/research hierarchy
- Create remotely: /home/kangye/.config/research-workspace/env.sh
- Modify remotely: /home/kangye/.bashrc with one managed source block

- [ ] **Step 1: Install without overwriting another skill**

If the destination is absent:

~~~bash
ln -s \
  "$HOME/.config/superpowers/worktrees/organizing-ai-research-workspaces/agent-research-workspace-skill/skills/organizing-ai-research-workspaces" \
  "$HOME/.codex/skills/organizing-ai-research-workspaces"
~~~

If present, verify it resolves to the same source; stop rather than overwrite anything else.

- [ ] **Step 2: Re-inspect storage and permissions**

~~~bash
ssh -o ClearAllForwardings=yes volcengine3 \
  'id; findmnt -T "$HOME"; df -hT "$HOME"; namei -l "$HOME" /data /data1 /data2 /data3'
~~~

Expected: /home/kangye remains on /dev/nvme3n1 and is the safe writable root.

- [ ] **Step 3: Copy, dry-run, and apply the CLI**

~~~bash
scp skills/organizing-ai-research-workspaces/scripts/setup_workspace.py \
  volcengine3:/tmp/setup_research_workspace.py
ssh -o ClearAllForwardings=yes volcengine3 \
  'python3 /tmp/setup_research_workspace.py --root "$HOME/research" --env-file "$HOME/.config/research-workspace/env.sh" --shell-rc "$HOME/.bashrc" --dry-run'
ssh -o ClearAllForwardings=yes volcengine3 \
  'python3 /tmp/setup_research_workspace.py --root "$HOME/research" --env-file "$HOME/.config/research-workspace/env.sh" --shell-rc "$HOME/.bashrc"'
~~~

Expected: dry-run proposes only the approved hierarchy, env file, and one managed shell block; apply succeeds.

- [ ] **Step 4: Verify structure, environment, filesystem, ownership, and idempotency**

~~~bash
ssh -o ClearAllForwardings=yes volcengine3 '
  find "$HOME/research" -mindepth 1 -maxdepth 3 -type d -print | sort
  sed -n "/# >>> research-workspace >>>/,/# <<< research-workspace <<</p" "$HOME/.bashrc"
  bash -ic "printf \"%s\n\" \"\$RESEARCH_ROOT\" \"\$RUNS_ROOT\""
  findmnt -T "$HOME/research/runs"
  namei -l "$HOME/research" "$HOME/research/runs"
  python3 /tmp/setup_research_workspace.py --root "$HOME/research" --env-file "$HOME/.config/research-workspace/env.sh" --shell-rc "$HOME/.bashrc"
'
~~~

Expected: exactly the six directories below research, variables resolve to home-backed paths, storage is /dev/nvme3n1, directories are user-owned, and the second setup contains only UNCHANGED actions.

- [ ] **Step 5: Remove only the transient installer**

~~~bash
ssh -o ClearAllForwardings=yes volcengine3 'rm -f /tmp/setup_research_workspace.py'
~~~

### Task 8: Final verification and handoff

**Files:**
- No changes expected unless verification finds a defect.

- [ ] **Step 1: Run fresh local verification**

~~~bash
python3 -m unittest discover -s tests -v
python3 /Users/jky/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/organizing-ai-research-workspaces
git diff --check main...HEAD
git status -sb
~~~

Expected: 9 tests pass, validator succeeds, and no unstaged implementation changes remain.

- [ ] **Step 2: Report evidence**

Report the repository URL, branch, commits, PR URL, test count, skill installation path, remote directory tree, selected filesystem, permissions, environment values, and idempotency output. Do not claim completion without fresh command evidence.
