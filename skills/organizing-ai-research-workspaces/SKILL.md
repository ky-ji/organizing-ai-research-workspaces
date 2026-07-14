---
name: organizing-ai-research-workspaces
description: Use when setting up, auditing, or simplifying AI/ML research storage across laptops, GitHub, GPU servers, or clusters, especially when projects share datasets and pretrained weights or produce many runs and checkpoints.
---

# Organizing AI Research Workspaces

## Overview

Keep the logical structure small and make every paper result traceable by reference. Separate Git projects, shared inputs, run outputs, and disposable scratch data without adding lifecycle hierarchies.

## Workflow

1. Inspect before mutating: identify the user, mounts, filesystems, free space, inode usage, ownership, mode, ACLs, bind mounts, symlinks, and actual write access.
2. Choose the safest currently writable root with adequate capacity. Treat root-owned empty disks as unavailable until a user-owned directory exists.
3. Present the mapping, risks, and tradeoffs. For audit-only requests, report the mapping and risks, then stop.
4. Run setup only when the user requests setup or apply. Require confirmation before destructive cleanup or changing shared permissions.
5. Create the contract with the bundled setup script, then verify structure, environment variables, filesystem identity, ownership, and a second idempotent run.

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

Do not add active, submitted, published, deprecated, or archived project layers. Make each potential paper one Git repository directly under `projects/`. Use this minimal project shape:

~~~text
projects/<project>/
├── README.md
├── src/
├── configs/
├── scripts/
├── results/
├── paper/
├── pyproject.toml
└── .gitignore
~~~

Add `tests/` or `notebooks/` only when the project needs them. Keep one canonical location for each shared dataset and externally obtained pretrained weight under `shared/` within each workspace on each machine; do not interpret this as one global copy across machines. Treat `scratch/` as disposable.

## Runs and Checkpoints

Use `runs/<project>/<run-id>/` with run IDs shaped as `YYYYMMDD-HHMM_<git-sha7>_<purpose>`. Keep resolved configuration, metadata, metrics, logs, and `runs/<project>/<run-id>/checkpoints/` together.

Retain `last` plus the best one or few checkpoints. Keep a paper-selected model in its original run. Track only its run ID and relative checkpoint name in the project repository's `results/paper-runs.yaml`, and add a `KEEP` marker to that run. Do not create a separate paper-model copy by default.

## Git Boundary

| Track in Git | Keep outside Git |
|---|---|
| Code, configs, environment locks, paper source, small results, run references | Datasets, downloaded weights, checkpoints, full logs, caches, secrets |

Never hardcode machine paths in project code. Resolve storage from `RESEARCH_ROOT`, `PROJECTS_ROOT`, `SHARED_ROOT`, `DATASETS_ROOT`, `PRETRAINED_ROOT`, `RUNS_ROOT`, and `SCRATCH_ROOT`.

## Storage Safety

Reject a world-writable directory without the sticky bit for unique checkpoints: another user may rename or delete entries. Do not infer usability from capacity alone; inspect complete path permissions and ACLs. Prefer a safe home-backed NVMe now over an inaccessible empty disk. Move physical storage later only behind the same logical variables.

Treat backups, archive trees, DVC, MLflow, W&B, object storage, and model registries as opt-in only. Introduce them only when the user explicitly requests their tradeoffs.

## Example

After confirming that home is the safe large filesystem, set `SKILL_DIR` to the absolute directory containing this `SKILL.md`, using the path by which the skill was loaded. Do not assume the current working directory. Then run:

~~~bash
python3 "$SKILL_DIR/scripts/setup_workspace.py" \
  --root "$HOME/research" \
  --env-file "$HOME/.config/research-workspace/env.sh"
. "$HOME/.config/research-workspace/env.sh"
~~~

Keep `--shell-rc` as an explicit opt-in. Omit it by default; identify the user's shell and correct startup file before adding it.

Source the env file before checking variables. The `findmnt -T "$RUNS_ROOT"` and `namei -l "$RUNS_ROOT"` checks are Linux-only; use platform equivalents elsewhere. Run the setup command again and require it to report only `UNCHANGED` actions.

## Quick Reference

| Question | Default |
|---|---|
| Where does code live? | `projects/<paper>/` |
| Where are shared inputs? | `shared/datasets/` and `shared/pretrained/` |
| Where is a checkpoint? | Its originating run |
| How is a paper model retained? | `paper-runs.yaml` plus `KEEP` |
| What may be deleted freely? | `scratch/` |

## Red Flags and Common Mistakes

Stop if a proposal adds status folders, a model registry, a backup policy, or an archive without being asked; writes to a mount root because it looks empty; hardcodes `/home` or `/data` paths in project code; commits checkpoints to Git; or calls setup complete without verifying a second run.
