# Organizing AI Research Workspaces

> A small, opinionated system for keeping AI research code, shared data, experiment runs, and checkpoints traceable across machines.

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)

AI research rarely stays on one computer. A paper may move between GitHub, a laptop, several GPU servers, and a cluster while sharing datasets and pretrained weights with other projects. This repository provides a deliberately simple directory contract, a safe setup tool, and a Codex skill for applying the method consistently.

**中文简介：** 这是一套面向 AI 研究者的简洁文件管理方法。它把论文项目、共享数据、训练输出和临时文件分开，并明确 checkpoint 应放在哪里；默认不增加项目归档层、论文模型副本或模型 registry。

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

Use an **audit before apply** workflow. Begin with `--dry-run`, inspect every proposed action, and apply only when the selected root is safe and writable.

```bash
git clone https://github.com/ky-ji/organizing-ai-research-workspaces.git
cd organizing-ai-research-workspaces

SETUP_SCRIPT="$PWD/skills/organizing-ai-research-workspaces/scripts/setup_workspace.py"

# Preview: no files or directories are changed.
python3 "$SETUP_SCRIPT" \
  --root "$HOME/research" \
  --env-file "$HOME/.config/research-workspace/env.sh" \
  --dry-run

# Apply after reviewing the preview.
python3 "$SETUP_SCRIPT" \
  --root "$HOME/research" \
  --env-file "$HOME/.config/research-workspace/env.sh"

. "$HOME/.config/research-workspace/env.sh"

# Verify idempotence: every line should say UNCHANGED.
python3 "$SETUP_SCRIPT" \
  --root "$HOME/research" \
  --env-file "$HOME/.config/research-workspace/env.sh"
```

Shell startup files are not edited by default. `--shell-rc` is an explicit opt-in; identify the user's actual shell and correct startup file before enabling it.

The setup tool preflights file collisions, symlink aliases, hard-linked outputs, and overlapping logical directories before mutation. Managed files are replaced atomically so an interrupted write does not truncate the previous version.

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

Use run IDs shaped as `YYYYMMDD-HHMM_<git-sha7>_<purpose>`. Keep the resolved configuration, metadata, metrics, logs, and checkpoints together in the same run.

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

Useful read-only checks on Linux include:

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

The reusable skill lives at [`skills/organizing-ai-research-workspaces/`](skills/organizing-ai-research-workspaces/). Ask Codex to install that directory from this GitHub repository, then invoke `$organizing-ai-research-workspaces` when auditing or configuring a laptop, GPU server, or cluster.

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
├── test_setup_workspace.py
└── test_skill_contract.py
```

- [`SKILL.md`](skills/organizing-ai-research-workspaces/SKILL.md) contains the methodology and agent workflow.
- [`setup_workspace.py`](skills/organizing-ai-research-workspaces/scripts/setup_workspace.py) implements safe, idempotent setup.
- [`tests/`](tests/) protects the directory, collision, atomic-write, and idempotence contracts.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=/tmp/research-workspace-pycache \
  python3 -m py_compile skills/organizing-ai-research-workspaces/scripts/setup_workspace.py
```

The skill also passes Codex's official `skill-creator` validator.

## Contributing

Issues and focused pull requests are welcome. Please preserve the project's core constraint: new default complexity must solve a demonstrated research-storage problem. Changes to the setup tool should include a regression test and retain dry-run, preflight, and idempotence behavior.

## License

No open-source license has been selected yet. Until a license is added, the repository is publicly readable but does not grant permission to copy, modify, or redistribute the work.
