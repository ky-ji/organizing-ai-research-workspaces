# Organizing AI Research Workspaces — Skill Design

## Goal

Create a reusable agent skill that sets up and maintains a deliberately simple filesystem methodology for an AI PhD working across laptops, GitHub, GPU servers, and clusters. The skill must keep paper projects, shared datasets and pretrained weights, experiment runs, and checkpoints traceable without introducing project archives, model registries, or separate paper-model backups.

## Public-skill review

The public skill search covered research project organization, reproducible research, ML experiment management, checkpoint management, AI research project structure, and scientific experiment organization.

- `delphine-l/claude_global@folder-organization` is the closest match, but adds `archives`, `deprecated`, session-save hierarchies, per-directory manifests, and broad templates that conflict with the requested minimal structure.
- `omer-metin/skills-for-antigravity@data-reproducibility` contains useful ideas about environment variables, seeds, data hashes, and experiment manifests, but its trigger metadata is malformed and its advice is broader than folder management.
- `mindrally/skills@machine-learning` is JAX-specific and does not manage research storage.
- `alphaonedev/openclaw-graph@mlflow` assumes an MLflow service and model lifecycle that the user explicitly does not want.
- Generic `project-structure` skills focus on software colocation or web/backend layouts rather than cross-machine AI research data and checkpoint boundaries.

The new skill will therefore remain independent while adopting only two proven ideas from the public candidates: predictable naming and environment-variable-based paths.

## RED baseline findings

Three agents were asked to solve representative tasks without the new skill.

1. The multi-machine answer was broadly competent but introduced a top-level `models` directory, an `artifacts` directory inside every run, and optional project directories by default. This drifted from the exact four-root methodology.
2. The server answer correctly detected the unsafe world-writable `/data` root, but recommended currently inaccessible `/data1` and `/data2` as the main layout instead of preferring an immediately writable safe root and treating dedicated mounts as an optional later mapping.
3. The checkpoint answer expanded into `Scratch`, `Candidate`, `Paper-bound`, and `Retired` states, automatic retention windows, paper IDs, annotated tags, and hash verification. This was substantially more complex than requested.

The skill must prevent these predictable forms of over-design.

## Methodology contract

The logical workspace contains exactly four top-level entries:

```text
research/
├── projects/
├── shared/
│   ├── datasets/
│   └── pretrained/
├── runs/
└── scratch/
```

Rules:

- Each potential paper is one Git repository under `projects/`.
- Projects are never moved into active, submitted, published, deprecated, or archived directory layers.
- Shared datasets and externally obtained pretrained weights each have one canonical copy under `shared/`.
- Every training checkpoint remains under its originating `runs/<project>/<run-id>/checkpoints/` directory.
- A paper-selected checkpoint is not copied into an artifact registry or backup directory. A Git-tracked `results/paper-runs.yaml` records its run ID and relative checkpoint name; a `KEEP` marker protects the run from routine cleanup.
- Git tracks code, configuration, environment definitions, paper sources, small results, and run references. Git does not track datasets, downloaded weights, checkpoints, complete logs, caches, or secrets.
- Cross-machine code resolves paths through environment variables rather than machine-specific absolute paths.
- `scratch/` is explicitly disposable.

The skill must treat backup, archival, DVC, MLflow, W&B, model registries, and object storage as opt-in extensions only when explicitly requested.

## Project and run shapes

The recommended project shape is minimal:

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

`tests/` and `notebooks/` are created only when the project actually needs them.

Run IDs use:

```text
YYYYMMDD-HHMM_<git-sha7>_<purpose>
```

Each run keeps its resolved configuration, metadata, metrics, logs, and checkpoints together. Checkpoint retention defaults to `last` plus the best one or few models; the skill does not impose multi-stage lifecycle terminology.

## Server inspection and placement

Before changing a machine, the skill checks:

- the current user and home directory;
- device, filesystem, mount point, free space, and inode usage for candidate paths;
- ownership, mode, ACLs, and write access;
- whether a world-writable directory has the sticky bit;
- whether the proposed path is a bind mount or symlink.

The default is the safest currently writable location with enough space. A root-owned empty disk is not treated as usable until a user-owned subdirectory exists. A world-writable root without the sticky bit is rejected for unique checkpoints.

For `volcengine3`, the initial mapping is intentionally simple because `/home/kangye` is on `/dev/nvme3n1` with ample free space:

```text
RESEARCH_ROOT=/home/kangye/research
PROJECTS_ROOT=/home/kangye/research/projects
SHARED_ROOT=/home/kangye/research/shared
DATASETS_ROOT=/home/kangye/research/shared/datasets
PRETRAINED_ROOT=/home/kangye/research/shared/pretrained
RUNS_ROOT=/home/kangye/research/runs
SCRATCH_ROOT=/home/kangye/research/scratch
```

Dedicated `/data1` or `/data2` placement remains a future option after an administrator creates correctly owned subdirectories.

## Skill package

The repository separates the installable skill from development material:

```text
skills/organizing-ai-research-workspaces/
├── SKILL.md
├── agents/openai.yaml
└── scripts/setup_workspace.py
tests/
├── test_setup_workspace.py
└── test_skill_contract.py
docs/superpowers/
├── specs/
└── plans/
```

`SKILL.md` contains the decision workflow, exact directory contract, checkpoint policy, Git boundary, quick reference, and common mistakes. `setup_workspace.py` performs deterministic, idempotent directory and environment-file creation. It does not create project archives, model backups, or modify shell startup files unless explicitly requested.

## Setup-script interface

The script accepts:

```text
setup_workspace.py --root PATH [--env-file PATH] [--shell-rc PATH] [--dry-run]
```

Behavior:

- expand `~` and resolve the requested root;
- create the exact required directories;
- write an idempotent shell environment file with the seven logical root variables;
- when `--shell-rc` is explicitly provided, add one idempotent source line without disturbing existing shell configuration;
- refuse if a required directory path is occupied by a non-directory;
- produce no duplicate content on repeated execution;
- make no shell-rc edits by default;
- support dry-run without filesystem changes.

## Validation

Validation has four layers:

1. RED/GREEN unit tests for dry-run, exact directory creation, environment content, idempotency, and path-conflict failure.
2. A skill-contract test that checks required concepts and rejects forbidden default hierarchy names such as project archive layers and paper-model registry paths.
3. The official `quick_validate.py` validator for skill metadata and folder shape.
4. Forward tests that rerun the three baseline scenarios with the new skill and verify that the answers remain simple, safe, and consistent.

## Publication and installation

Create a standalone repository named `organizing-ai-research-workspaces`, publish it under the authenticated GitHub account, and install the nested skill into the local Codex skill directory. Branch names must not use the `codex/` prefix.

After validation, invoke the new skill against `volcengine3`, run the setup script in the confirmed home-backed location, and verify directory identity, environment-file content, permissions, filesystem mapping, and idempotency.
