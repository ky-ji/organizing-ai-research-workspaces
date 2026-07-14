# Project README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an English-first, Chinese-friendly README that presents the repository as a polished AI research workspace methodology with an executable setup tool.

**Architecture:** Keep the product story in one root `README.md` and protect its non-negotiable claims with a focused `unittest` contract. Reuse the existing skill and CLI as the source of truth, validate the documented quick start in a temporary home, then update the existing Draft PR and GitHub repository metadata.

**Tech Stack:** GitHub-flavored Markdown, Python 3.10+, `unittest`, existing setup CLI, GitHub CLI.

---

## File Map

- Create `README.md`: public project landing page and quick-start guide.
- Create `tests/test_readme_contract.py`: stable README structure, safety, checkpoint, and link contracts.
- Modify no production code: the README must describe the already-tested behavior rather than changing it.
- Update GitHub metadata and Draft PR #1 after local verification.

### Task 1: Define the README Contract

**Files:**
- Create: `tests/test_readme_contract.py`

- [ ] **Step 1: Add the failing contract test**

Create `tests/test_readme_contract.py` with:

```python
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"


class ReadmeContractTests(unittest.TestCase):
    def _read_readme(self):
        self.assertTrue(README.is_file(), "README.md must exist at repository root")
        return README.read_text(encoding="utf-8")

    def test_readme_has_the_project_narrative_and_exact_contract(self):
        contents = self._read_readme()
        for heading in (
            "# Organizing AI Research Workspaces",
            "## Why this exists",
            "## The four-root workspace",
            "## Quick start",
            "## Organizing paper projects",
            "## Where checkpoints go",
            "## Git and paths across machines",
            "## Storage safety",
            "## Deliberate non-goals",
            "## Use it as a Codex skill",
            "## Repository structure",
            "## Validation",
            "## Contributing",
            "## License",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, contents)
        self.assertIn("中文", contents)

        tree_match = re.search(
            r"## The four-root workspace.*?```text\n(?P<tree>.*?)\n```",
            contents,
            re.DOTALL,
        )
        self.assertIsNotNone(tree_match)
        self.assertEqual(
            tree_match.group("tree").splitlines(),
            [
                "research/",
                "├── projects/",
                "├── shared/",
                "│   ├── datasets/",
                "│   └── pretrained/",
                "├── runs/",
                "└── scratch/",
            ],
        )
        self.assertLessEqual(len(contents.split()), 1800)
        self.assertIsNone(re.search(r"\b(?:TBD|TODO|FIXME|XXX)\b", contents))

    def test_quick_start_and_checkpoint_policy_are_safe(self):
        contents = self._read_readme()
        quick_start = re.search(
            r"## Quick start\n(?P<body>.*?)(?=\n## )", contents, re.DOTALL
        )
        self.assertIsNotNone(quick_start)
        body = quick_start.group("body")
        code = "\n".join(re.findall(r"```bash\n(.*?)\n```", body, re.DOTALL))
        self.assertIn("git clone https://github.com/ky-ji/organizing-ai-research-workspaces.git", code)
        self.assertIn("--dry-run", code)
        self.assertGreaterEqual(code.count('python3 "$SETUP_SCRIPT"'), 3)
        self.assertIn('. "$HOME/.config/research-workspace/env.sh"', code)
        self.assertNotIn("--shell-rc", code)

        for required_text in (
            "$RUNS_ROOT/<project>/<run-id>/checkpoints/",
            "results/paper-runs.yaml",
            "KEEP",
            "Retain `last` plus the best one or few checkpoints",
            "Do not create a separate paper-model copy",
            "world-writable directory without the sticky bit",
            "audit before apply",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, contents)

    def test_internal_markdown_links_resolve(self):
        contents = self._read_readme()
        links = re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", contents)
        internal_links = [
            link.split("#", 1)[0]
            for link in links
            if link
            and not link.startswith(("http://", "https://", "#", "mailto:"))
        ]
        self.assertTrue(internal_links, "README must link to repository files")
        for link in internal_links:
            with self.subTest(link=link):
                self.assertTrue((REPO_ROOT / link).exists(), f"broken link: {link}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_readme_contract -v
```

Expected: three errors or failures because root `README.md` does not exist.

- [ ] **Step 3: Commit the RED contract**

```bash
git add tests/test_readme_contract.py
git commit -m "test: define project README contract"
```

### Task 2: Write the Public README

**Files:**
- Create: `README.md`
- Test: `tests/test_readme_contract.py`

- [ ] **Step 1: Create `README.md` with the approved narrative**

Use this complete content, preserving the exact directory tree and safe quick-start order:

````markdown
# Organizing AI Research Workspaces

> A small, opinionated system for keeping AI research code, shared data, runs, and checkpoints traceable across machines.

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)

AI research rarely stays on one laptop. A paper may move between GitHub, a workstation, several GPU servers, and a cluster while sharing datasets and pretrained weights with other projects. This project provides one deliberately simple directory contract, a safe setup tool, and a Codex skill for applying the method without inventing a miniature MLOps platform.

**中文简介：** 这是一套面向 AI 研究者的简洁文件管理方法。它把论文项目、共享数据、训练输出和临时文件分开，并明确 checkpoint 应放在哪里；默认不增加归档层、论文模型副本或模型 registry。

## Why this exists

Most research storage problems are boundary problems:

- code gets mixed with multi-gigabyte outputs;
- the same dataset is copied into every project;
- checkpoints lose the configuration and commit that produced them;
- absolute `/home/...` or `/data/...` paths break on the next machine;
- an empty disk looks usable even when the researcher cannot safely write to it.

The solution here is intentionally boring: four logical roots, one Git repository per potential paper, and every run kept together with the evidence needed to understand it.

## The four-root workspace

```text
research/
├── projects/
├── shared/
│   ├── datasets/
│   └── pretrained/
├── runs/
└── scratch/
```

| Directory | Purpose |
|---|---|
| `projects/` | One Git repository per paper-oriented research project |
| `shared/` | Canonical locations for datasets and externally obtained pretrained weights on this machine |
| `runs/` | Configurations, metadata, metrics, logs, and checkpoints produced by experiments |
| `scratch/` | Disposable caches, temporary exports, and one-off intermediate files |

The physical disk may differ between machines. The logical contract stays the same.

## Quick start

The setup tool uses an **audit before apply** workflow. Start with `--dry-run`, inspect every proposed action, and apply only when the selected root is safe and writable.

```bash
git clone https://github.com/ky-ji/organizing-ai-research-workspaces.git
cd organizing-ai-research-workspaces

SETUP_SCRIPT="$PWD/skills/organizing-ai-research-workspaces/scripts/setup_workspace.py"

python3 "$SETUP_SCRIPT" \
  --root "$HOME/research" \
  --env-file "$HOME/.config/research-workspace/env.sh" \
  --dry-run

# Review the plan, then apply it.
python3 "$SETUP_SCRIPT" \
  --root "$HOME/research" \
  --env-file "$HOME/.config/research-workspace/env.sh"

. "$HOME/.config/research-workspace/env.sh"

# The second run should report only UNCHANGED actions.
python3 "$SETUP_SCRIPT" \
  --root "$HOME/research" \
  --env-file "$HOME/.config/research-workspace/env.sh"
```

Shell startup files are not edited by default. `--shell-rc` is an explicit opt-in; identify the user's actual shell and correct startup file before enabling it.

The setup tool is idempotent. It preflights file collisions, symlink aliases, hard-linked outputs, and overlapping logical directories before mutation. Managed files are replaced atomically so an interrupted write does not truncate the previous version.

## Organizing paper projects

Make each potential paper one repository directly under `projects/`:

```text
projects/<project>/
├── README.md
├── src/
├── configs/
├── scripts/
├── results/
├── paper/
├── pyproject.toml
└── .gitignore
```

Add `tests/` and `notebooks/` only when they earn their place. Do not add `active/`, `submitted/`, `published/`, or `archived/` status hierarchies.

## Where checkpoints go

Checkpoints belong to the run that produced them:

```text
$RUNS_ROOT/<project>/<run-id>/checkpoints/
```

Use run IDs shaped as `YYYYMMDD-HHMM_<git-sha7>_<purpose>`, and keep the resolved configuration, metadata, metrics, and logs beside `checkpoints/`.

Retain `last` plus the best one or few checkpoints. For a model used in a paper:

1. leave the checkpoint in its original run;
2. add a `KEEP` marker to that run;
3. record the run ID and relative checkpoint path in the project's `results/paper-runs.yaml`.

```yaml
main_model:
  run_id: 20260714-1530_a1b2c3d_final
  checkpoint: checkpoints/best.ckpt
```

Do not create a separate paper-model copy or model registry by default. The small Git-tracked reference is the durable connection between the paper and the original run.

## Git and paths across machines

| Track in Git | Keep outside Git |
|---|---|
| Code, configs, environment locks, paper source, small results, run references | Datasets, downloaded weights, checkpoints, full logs, caches, secrets |

Never hardcode a machine's storage path in project code. The generated environment file exports:

```text
RESEARCH_ROOT
PROJECTS_ROOT
SHARED_ROOT
DATASETS_ROOT
PRETRAINED_ROOT
RUNS_ROOT
SCRATCH_ROOT
```

Each machine can map those variables to its own safe storage while project code remains portable.

## Storage safety

Capacity alone does not make a location usable. Before choosing a root, inspect the current user, mount source, filesystem, free space, inode capacity, ownership, permissions, ACLs, symlinks, bind mounts, and actual write access.

On Linux, useful read-only checks include:

```bash
id
findmnt -T "$HOME"
df -hT "$HOME"
df -ih "$HOME"
namei -l "$HOME"
getfacl -p "$HOME" 2>/dev/null || true
```

Never place unique checkpoints in a world-writable directory without the sticky bit: another user may rename or delete them. Treat a root-owned empty disk as unavailable until an administrator creates a researcher-owned directory on it.

## Deliberate non-goals

The default method does **not** add:

- project status or archive trees;
- paper-model backup copies;
- DVC, MLflow, W&B, or an artifact/model registry;
- object storage or an automatic migration layer;
- a universal backup policy.

These tools can be valuable, but they should be explicit responses to real team requirements rather than prerequisites for organizing one researcher's work.

## Use it as a Codex skill

The reusable skill lives at [`skills/organizing-ai-research-workspaces/`](skills/organizing-ai-research-workspaces/). In Codex, ask it to install that skill from this GitHub repository, then use `$organizing-ai-research-workspaces` when auditing or configuring a laptop, GPU server, or cluster.

The skill preserves an important permission boundary: audit-only requests stop after reporting the mapping and risks; setup runs only after an explicit setup or apply request.

## Repository structure

```text
skills/organizing-ai-research-workspaces/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── setup_workspace.py
tests/
├── test_readme_contract.py
├── test_setup_workspace.py
└── test_skill_contract.py
```

- [`SKILL.md`](skills/organizing-ai-research-workspaces/SKILL.md) contains the methodology and agent workflow.
- [`setup_workspace.py`](skills/organizing-ai-research-workspaces/scripts/setup_workspace.py) implements safe, idempotent setup.
- [`tests/`](tests/) protects the directory, documentation, collision, atomic-write, and idempotence contracts.

## Validation

Run the complete test suite with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 -m py_compile skills/organizing-ai-research-workspaces/scripts/setup_workspace.py
```

The skill also passes Codex's official `skill-creator` validator.

## Contributing

Issues and focused pull requests are welcome. Please preserve the project's core constraint: new default complexity must solve a demonstrated research-storage problem. Changes to the setup tool should include a regression test and retain dry-run, preflight, and idempotence behavior.

## License

No open-source license has been selected yet. Until a license is added, the repository is publicly readable but does not grant permission to copy, modify, or redistribute the work.
````

- [ ] **Step 2: Run the README contract**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_readme_contract -v
```

Expected: three tests pass.

- [ ] **Step 3: Run the full suite**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Expected: twelve tests pass.

- [ ] **Step 4: Commit the README**

```bash
git add README.md
git commit -m "docs: add project README"
```

### Task 3: Verify the Documented Workflow

**Files:**
- Verify: `README.md`
- Verify: `skills/organizing-ai-research-workspaces/scripts/setup_workspace.py`

- [ ] **Step 1: Run the CLI help check**

```bash
python3 skills/organizing-ai-research-workspaces/scripts/setup_workspace.py --help
```

Expected: help lists `--root`, `--env-file`, `--shell-rc`, and `--dry-run`.

- [ ] **Step 2: Smoke-test dry-run, apply, and idempotence in a temporary home**

```bash
tmp_home=$(mktemp -d)
script="$PWD/skills/organizing-ai-research-workspaces/scripts/setup_workspace.py"
python3 "$script" --root "$tmp_home/research" --env-file "$tmp_home/.config/research-workspace/env.sh" --dry-run
python3 "$script" --root "$tmp_home/research" --env-file "$tmp_home/.config/research-workspace/env.sh"
python3 "$script" --root "$tmp_home/research" --env-file "$tmp_home/.config/research-workspace/env.sh"
rm -rf "$tmp_home"
```

Expected: dry-run reports planned creation without writing; apply creates the contract; the final run reports eight `UNCHANGED` actions because no shell rc is managed.

- [ ] **Step 3: Run document and repository checks**

```bash
! rg -n '\b(TBD|TODO|FIXME|XXX)\b' README.md tests/test_readme_contract.py
git diff --check main...HEAD
test -z "$(git status --short)"
```

Expected: no placeholders, whitespace errors, or uncommitted files.

### Task 4: Publish the README Update

**Files:**
- Update remote repository metadata.
- Update existing Draft PR #1.

- [ ] **Step 1: Push the feature branch**

```bash
git push origin agent/research-workspace-skill
```

Expected: remote head equals local `HEAD`.

- [ ] **Step 2: Improve truthful repository metadata**

```bash
gh repo edit ky-ji/organizing-ai-research-workspaces \
  --description "A simple, traceable workspace methodology and setup tool for AI research projects, shared data, runs, and checkpoints." \
  --add-topic ai-research \
  --add-topic research-workflow \
  --add-topic checkpoint-management \
  --add-topic reproducible-research \
  --add-topic codex-skill
```

Expected: the public repository reports the new description and five topics.

- [ ] **Step 3: Update Draft PR #1**

Replace the PR body with a summary that includes the new README, then verify:

```bash
gh pr view 1 --json isDraft,state,url,headRefOid
```

Expected: PR #1 remains open and draft, and `headRefOid` equals local `HEAD`.

- [ ] **Step 4: Final verification**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
git diff --check main...HEAD
git status --short --branch
```

Expected: twelve tests pass, diff check succeeds, and the feature branch is clean and synchronized with origin.
