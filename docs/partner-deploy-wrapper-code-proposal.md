# mpc-infra Phase 3 Code Proposal

Date: 2026-03-23
Repo: `sig-net/mpc-infrastructure`
Scope: concrete file-level proposal for introducing the `mpc-infra` wrapper into this repository

## Executive summary

This phase proposes introducing `mpc-infra` as a **new tool directory** inside `sig-net/mpc-infrastructure`, without changing the existing `terraform/partner-mainnet` implementation yet.

The wrapper should initially be additive:

- it reads a partner-friendly config file
- validates environment and secrets
- renders generated Terraform inputs
- orchestrates the existing `terraform/partner-mainnet` workflow
- leaves current raw Terraform flows available as a fallback during rollout

This is the safest way to start because it gives the team a concrete implementation path without immediately rewriting the infrastructure module.

## Proposed repository additions

```text
docs/
  partner-deploy-wrapper-design.md
  partner-deploy-wrapper-toolset.md
  partner-deploy-wrapper-code-proposal.md

tools/mpc_infra/
  README.md
  pyproject.toml
  src/mpc_infra/__init__.py
  src/mpc_infra/cli.py
  src/mpc_infra/config.py
  src/mpc_infra/constants.py
  src/mpc_infra/gcloud.py
  src/mpc_infra/render.py
  src/mpc_infra/terraform.py
  src/mpc_infra/validate.py
  src/mpc_infra/upgrade.py
  src/mpc_infra/models.py
  tests/
    test_config.py
    test_render.py
```

## Why place the wrapper under `tools/`

That keeps the wrapper clearly separate from:

- Terraform source
- helper shell scripts
- docs-only content

It also leaves room for future repo-local tools without polluting the Terraform directories.

## Proposed command layout

The initial CLI surface should be:

```bash
mpc-infra init
mpc-infra validate
mpc-infra plan
mpc-infra deploy
mpc-infra status
mpc-infra upgrade
```

## Command behavior proposal

### `init`

Responsibilities:

- create a starter config file
- apply supported defaults
- prompt for the small set of required values
- avoid exposing raw Terraform structure if possible

Output:

- `partner-mainnet.yaml` or similar config file

### `validate`

Responsibilities:

- check local tool availability
- validate config schema
- validate GCP auth/project
- validate required APIs
- validate Secret Manager secret existence
- validate Terraform state bucket existence

Output:

- pass/fail summary
- actionable remediation messages

### `plan`

Responsibilities:

- render generated Terraform inputs
- run Terraform init/plan in `terraform/partner-mainnet`
- summarize high-level changes

Generated artifact proposal:

```text
terraform/partner-mainnet/generated.auto.tfvars.json
```

That file should be tool-owned and reproducible.

### `deploy`

Responsibilities:

- require a valid config
- require successful validation first
- render generated Terraform inputs
- run the deploy path in a controlled way
- print post-deploy DNS and verification guidance

### `status`

Responsibilities:

- read Terraform outputs
- resolve useful deployment metadata
- print instance names, load balancer IPs, and next checks

### `upgrade`

Responsibilities:

- detect current deployed image tag
- resolve latest published release tag by default
- support `--tag <tag>` override
- compare current and target release contract metadata
- detect newly required env/secret contract changes
- prompt for missing secret values when needed
- create missing secrets in GCP Secret Manager
- write the updated image selection into generated inputs or config
- run plan/deploy path
- print post-upgrade verification steps

## Config strategy

The wrapper should use a stable partner-facing YAML file.

Proposed filename:

```text
partner-mainnet.yaml
```

That config should not mirror Terraform one-for-one. It should instead reflect partner intent.

### Proposed data model

Top-level:

- schema version
- profile (`mainnet`)
- project/region/zone
- state bucket
- nodes list
- optional image override

Per-node:

- account ID
- domain
- secret references

### Important design choice

The wrapper should translate partner config into Terraform shape rather than making partners edit Terraform variable files directly.

## Generated artifact strategy

The wrapper should own generated files, not user-authored files.

Proposed generated file:

```text
terraform/partner-mainnet/generated.auto.tfvars.json
```

Properties:

- deterministic
- machine-generated
- clearly documented as tool-owned
- safe to overwrite
- ignored or documented appropriately in git workflow

The existing example tfvars file can remain as a legacy/manual path until the wrapper becomes the default.

## Module responsibilities

### `cli.py`

Defines Typer commands and top-level UX.

### `models.py`

Contains Pydantic models for:

- partner config
- node config
- secret references
- validation result structures

### `config.py`

Handles:

- loading YAML
- writing starter configs
- version checks
- config normalization

### `constants.py`

Centralizes:

- default region and zone
- required APIs
- required secret keys
- Terraform working directory path
- generated filename constants

### `gcloud.py`

Thin wrapper for:

- active auth/account checks
- project existence checks
- API checks
- Secret Manager lookups
- optional later bootstrap helpers

### `render.py`

Maps partner config into Terraform input JSON.

This is the most important translation layer.

### `terraform.py`

Thin wrapper for:

- init
- plan
- apply/deploy path
- output parsing

This module should keep Terraform invocation consistent and centralized.

### `validate.py`

Aggregates checks from config and GCP helpers into a single validation report.

### `upgrade.py`

Handles:

- current image detection
- release resolution
- target tag selection
- release contract comparison
- missing secret detection
- guided secret creation planning
- update planning

## Proposed implementation order

### Step 1: package skeleton

Add the package structure and CLI entrypoint.

### Step 2: config models and loader

Implement:

- config schema
- config file read/write
- starter config generation

### Step 3: Terraform renderer

Implement rendering from partner YAML to `generated.auto.tfvars.json`.

### Step 4: validation engine

Implement the high-value checks first:

- tools available
- project exists
- APIs enabled
- state bucket exists
- required secrets exist

### Step 5: plan/deploy/status wiring

Add command orchestration over the existing Terraform module.

### Step 6: upgrade support

Add release tag resolution and controlled image updates.

## What should remain unchanged in the first implementation

To reduce risk, phase 3 should **not** yet:

- rewrite `terraform/partner-mainnet`
- remove the current manual Terraform flow
- move partner deployments to Kubernetes
- redesign all secrets or node variable semantics

The wrapper should adapt to the current Terraform implementation first.

## Compatibility approach

The safest early model is:

- wrapper path = recommended
- raw Terraform path = still possible for internal fallback/debugging

That gives the team a gradual migration path.

## Testing recommendations

At minimum, add tests for:

- config loading/validation
- generated tfvars content
- missing required secret mapping
- invalid domain / missing required fields

Mock `gcloud` and `terraform` subprocess output rather than invoking live infrastructure in unit tests.

## Future extension points

The proposed module layout keeps room for later additions such as:

- greenfield bootstrap helpers
- environment profile support beyond mainnet
- richer status output
- release channel support (`stable`, `candidate`)
- migration helpers for config schema changes
- richer release manifests that describe env/secret migrations for upgrades

## Recommendation

Proceed with:

1. additive tool introduction under `tools/mpc_infra/`
2. generated Terraform input flow
3. strong preflight validation
4. no immediate rewrite of `terraform/partner-mainnet`

That gives the repo a concrete implementation path while keeping deployment risk low.
