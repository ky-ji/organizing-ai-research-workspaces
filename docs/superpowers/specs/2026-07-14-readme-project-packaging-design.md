# README Project Packaging Design

## Goal

Present `organizing-ai-research-workspaces` as a credible, useful open-source project for AI researchers who work across laptops, GitHub, GPU servers, and clusters. The README should make the method understandable in under a minute and make the safe setup workflow executable without overselling the project.

## Audience and Positioning

The primary audience is AI/ML PhD students and research engineers managing multiple paper-oriented projects, shared datasets, pretrained weights, experiment runs, and checkpoints.

Position the repository as an **AI research workspace methodology with an executable setup tool**. Treat the Codex skill as a useful delivery format, not as the entire identity of the project.

Use English for the main README and include one short Chinese introduction near the top. Keep the voice practical, calm, and opinionated: simple defaults, explicit boundaries, and traceable results.

## Narrative

Use a problem-to-method-to-action flow:

1. Open with the project name and a concise tagline about simple, traceable AI research storage.
2. State the recurring problem: code, shared inputs, runs, and checkpoints become mixed across machines.
3. Show the four-root directory contract immediately.
4. Explain why the separation works and what deliberately remains outside the default design.
5. Provide a verified quick start using the bundled setup script, first as a dry run and then as an explicit apply step.
6. Explain project layout, Git boundaries, environment variables, storage safety, and checkpoint retention.
7. End with repository contents, validation commands, contribution guidance, and the license state without inventing a license.

## README Structure

Use these sections in this order:

- Hero: title, tagline, truthful status badges, short English summary, short Chinese summary
- Why this exists
- The four-root workspace contract
- Quick start
- How projects are organized
- Where checkpoints go
- Git and cross-machine path boundaries
- Storage safety
- Deliberate non-goals
- Using it as a Codex skill
- Repository structure
- Validation
- Contributing and license note

The checkpoint section must be visually easy to find and must state:

- store checkpoints at `$RUNS_ROOT/<project>/<run-id>/checkpoints/`;
- retain `last` plus the best one or few checkpoints;
- keep a paper-selected checkpoint in its original run;
- record the run ID and relative checkpoint path in `results/paper-runs.yaml`;
- add a `KEEP` marker;
- do not create a default paper-model copy or registry.

## Quick Start Design

Use commands that work from a fresh clone. Resolve the bundled setup script from the cloned repository rather than assuming a globally installed skill. Show:

1. clone and enter the repository;
2. run `--dry-run` against `$HOME/research` and an environment file;
3. run the same command without `--dry-run` only after reviewing the plan;
4. source the generated environment file;
5. rerun setup and require only `UNCHANGED` output.

Do not modify a shell startup file in the default quick start. Explain that `--shell-rc` is opt-in and requires selecting the correct shell startup file.

## Visual and Marketing Constraints

Use the directory tree and compact tables as the primary visuals. Do not add decorative banners, screenshots, emojis in every heading, or unverified claims. Use only badges backed by real repository state, such as Python version or test workflow status if the referenced workflow exists. Do not display fabricated stars, downloads, coverage, publication, or production-readiness claims.

## Safety and Error Communication

Make the audit-before-apply boundary explicit. State that a large disk is not automatically safe or writable. Mention ownership, permissions, ACLs, symlinks, bind mounts, inode capacity, and the danger of a world-writable directory without the sticky bit.

Document that the setup tool rejects path collisions and overlapping logical directories, performs managed-file updates atomically, and is designed to be idempotent. Avoid promising cross-filesystem transactions or automatic migration.

## Deliberate Non-Goals

Clearly state that the default method does not add project status folders, archives, paper-model backups, DVC, MLflow, W&B, object storage, or artifact/model registries. These remain explicit opt-ins when a research group actually needs their trade-offs.

## Validation and Acceptance Criteria

The finished README must:

- render as valid GitHub Markdown;
- be English-first with a concise Chinese introduction;
- include the exact four-root contract;
- provide commands consistent with the current CLI help and behavior;
- make the checkpoint answer discoverable without reading the whole file;
- distinguish dry-run from apply and keep shell modification opt-in;
- avoid claims not supported by repository files or fresh verification;
- contain no placeholders, dead internal links, or references to nonexistent workflows or licenses;
- remain concise enough to scan while still explaining the method's reasoning.

Verification will include the existing nine tests, official skill validation, CLI help/quick-start smoke tests in a temporary directory, Markdown link/placeholder checks, and `git diff --check`.
