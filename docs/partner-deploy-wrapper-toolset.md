# mpc-infra Toolset Proposal

Date: 2026-03-23
Repo: `sig-net/mpc-infrastructure`
Scope: recommended implementation toolset for phase 2 of the partner deployment wrapper effort

## Executive summary

The `mpc-infra` wrapper should be built with the smallest practical stack that gives the team:

- good validation ergonomics
- predictable local packaging
- easy GCP and Terraform integration
- low maintenance overhead
- a clean path to later features like `upgrade` and greenfield project bootstrap

The recommended toolset is:

- **Python 3.12+** for the CLI implementation
- **Typer** for the CLI framework
- **Pydantic** for config schema validation
- **PyYAML** for reading and writing partner config files
- **subprocess** for invoking `gcloud` and `terraform`
- **JSON output parsing** from `gcloud`/`terraform` where possible
- optional **rich** for better UX, but not required for phase 1

This keeps the wrapper easy to read, easy to ship, and aligned with tools operators are likely to already have or can install simply.

## Recommended language: Python

### Why Python is the best fit here

Python is the strongest default for this tool because it is:

- widely available on operator machines
- well suited for CLI and config tooling
- straightforward for subprocess orchestration
- easy to maintain by infra-oriented engineers
- fast enough for this kind of workflow

The wrapper is primarily doing:

- prompting
- validation
- file generation
- shell command orchestration
- JSON parsing
- plain-English summaries

That is exactly the kind of work Python handles well.

## Why not Rust for the wrapper

Rust would produce a nice standalone binary, but I would not choose it first here.

Reasons:

- slower iteration for a tool that will likely change quickly in early phases
- higher maintenance overhead for a deployment UX tool
- more friction when adding prompt/validation/reporting behavior rapidly

Rust only becomes compelling if you later decide this should be distributed as a very polished standalone binary with strict packaging requirements.

## Why not Bash

Bash is tempting for thin wrappers, but it becomes brittle quickly once you need:

- structured config files
- validation logic
- JSON transformations
- clear user-facing errors
- testable code

This project is already beyond what I would trust to a shell-script-first design.

## Proposed runtime dependencies

### Required

#### 1. Python 3.12+

Primary runtime for the wrapper.

#### 2. Typer

Use Typer to define commands like:

```bash
mpc-infra init
mpc-infra validate
mpc-infra plan
mpc-infra deploy
mpc-infra status
mpc-infra upgrade
```

Why Typer:

- simple command structure
- type-hint driven
- easy help output
- low boilerplate
- good fit for multi-command tools

#### 3. Pydantic

Use Pydantic models for:

- config file schema
- validation messages
- versioned config support
- future migration helpers

This is especially valuable because the partner config will evolve over time.

#### 4. PyYAML

Use YAML for the partner-facing config file and PyYAML for reading/writing it.

YAML is friendlier than raw Terraform variables for most operators.

### Optional but recommended

#### 5. Rich

Use Rich only if you want better:

- tables
- colored status messages
- validation summaries
- command step output

This is useful, but I would keep it optional in the first implementation.

## External tools the wrapper should rely on

The wrapper should orchestrate a small set of existing tools rather than reimplementing them.

### 1. `terraform`

Needed for:

- `init`
- `plan`
- deploy/apply path in partner usage
- `output`

The wrapper should control exactly how Terraform is invoked and should generate the inputs it uses.

### 2. `gcloud`

Needed for:

- auth checks
- project selection/validation
- API enablement checks
- Secret Manager queries
- Compute resource lookups
- later bootstrap work

This should be the primary GCP integration surface.

### 3. `git` (optional for wrapper runtime, useful for operator workflow)

Not strictly required for every command, but useful for:

- version reporting
- documenting expected repo state
- wrapper self-version awareness if run from source

## Config format recommendation

Use a versioned YAML file, for example:

```yaml
version: 1
profile: mainnet
project_id: partner-multichain
region: europe-west1
zone: europe-west1-b
state_bucket: multichain-terraform-partner
nodes:
  - account_id: company.near
    domain: mpc.company.com
    secrets:
      account_sk: multichain-account-sk-mainnet-0
      cipher_sk: multichain-cipher-sk-mainnet-0
      sign_sk: multichain-sign-sk-mainnet-0
      sk_share: multichain-sk-share-mainnet-0
      eth_account_sk: multichain-eth-account-sk-mainnet-0
      eth_consensus_rpc: multichain-eth-consensus-rpc-url-mainnet
      eth_execution_rpc: multichain-eth-execution-rpc-url-mainnet
      sol_account_sk: multichain-sol-account-sk-mainnet-0
      sol_rpc_http: multichain-sol-rpc-http-url-mainnet
      sol_rpc_ws: multichain-sol-rpc-ws-url-mainnet
      hydration_rpc_ws: multichain-hydration-rpc-ws-url-mainnet
      hydration_signer_uri: multichain-hydration-signer-uri-mainnet
```

The wrapper should generate a Terraform input artifact from this, ideally as a generated `.auto.tfvars.json` file or another deterministic output format.

## Command implementation approach

### `mpc-infra init`

Needs:

- interactive prompts
- config writing
- safe defaults

Typer + Pydantic + PyYAML are enough.

### `mpc-infra validate`

Needs:

- command execution
- JSON parsing
- strong error messages

Python subprocess + `gcloud --format=json` + Pydantic validation are enough.

### `mpc-infra plan`

Needs:

- config translation
- generated tfvars
- Terraform execution
- change summary

Python subprocess is enough.

### `mpc-infra deploy`

Needs:

- same as plan
- execution guards
- post-deploy reporting

Again, Python subprocess is enough.

### `mpc-infra status`

Needs:

- detect deployed/current image tag or release
- resolve the latest published release
- compare deployment posture against the latest release contract
- detect missing required secrets or other contract drift
- print a recommended next action
- optionally read deployment outputs and query Compute/GCLB state as needed

This can be done through a mix of generated config, `terraform output -json`, selective `gcloud` lookups, and release metadata resolution.

### `mpc-infra upgrade`

Needs:

- detect deployed/current image tag
- resolve target tag
- compare current and target release contract metadata
- detect newly required env/secret requirements introduced by the target release
- create missing GCP Secret Manager secrets interactively when needed
- update config or generated Terraform input
- run plan/deploy path
- print verification guidance

This is another good fit for Python orchestration.

## Release resolution for `upgrade`

The default `upgrade` path should use the latest published release, not just the latest registry artifact.

Preferred resolution order:

1. GitHub Releases in the canonical source repo
2. explicit version manifest maintained by the team
3. container registry lookup only if release discipline guarantees correctness

The wrapper should also support:

```bash
mpc-infra upgrade --tag <tag>
```

That is important for controlled partner support and incident handling.

## Release contract metadata for upgrades

To make upgrades safe, each release should publish machine-readable metadata that describes what a partner deployment must have before upgrading.

Suggested fields:

- release version
- image tag
- newly required env keys
- newly required secret keys
- suggested secret names
- human-readable descriptions for prompts

Example:

```json
{
  "version": "v1.2.3",
  "imageTag": "631a0b00085dfc167e115643f791e8eed2cac0cb",
  "requiredSecrets": [
    {
      "key": "hydration_rpc_ws",
      "secretNameSuggestion": "multichain-hydration-rpc-ws-url-mainnet",
      "description": "Hydration RPC websocket URL"
    },
    {
      "key": "hydration_signer_uri",
      "secretNameSuggestion": "multichain-hydration-signer-uri-mainnet",
      "description": "Hydration signer URI"
    }
  ]
}
```

The wrapper should consume this metadata to detect missing requirements before the upgrade is allowed to continue.

## Guided secret creation during upgrade

If a target release introduces a new required secret and that secret is missing in the partner project, `mpc-infra upgrade` should:

1. explain what changed in the target release
2. suggest a default secret name
3. prompt the operator for the secret value securely
4. create the missing secret in GCP Secret Manager
5. add the secret version
6. validate that the secret exists before continuing

This makes the upgrade workflow act like a migration assistant, not just an image bump helper.

## Packaging options

### Option A: Python package inside this repo

Best first step.

Pros:

- easy to build now
- low friction
- keeps implementation close to Terraform/docs
- easy to iterate

### Option B: pipx-installable package

Good medium-term option.

Pros:

- simple operator install story
- keeps commands clean
- still Python-based

### Option C: packaged standalone binary later

Possible later if needed, but unnecessary for the first implementation.

## Testing approach

The wrapper should have lightweight tests for:

- config schema validation
- tfvars generation
- secret requirement validation logic
- image tag parsing/resolution
- command guardrails

Recommended test stack:

- `pytest`
- fixture-based config samples
- mocked subprocess outputs for `gcloud` and `terraform`

This should be enough to keep the wrapper reliable without making it heavyweight.

## File layout proposal

A reasonable layout inside `sig-net/mpc-infrastructure` would be:

```text
tools/mpc_infra/
  pyproject.toml
  README.md
  src/mpc_infra/__init__.py
  src/mpc_infra/cli.py
  src/mpc_infra/config.py
  src/mpc_infra/gcloud.py
  src/mpc_infra/terraform.py
  src/mpc_infra/validate.py
  src/mpc_infra/upgrade.py
  src/mpc_infra/render.py
  tests/
```

This keeps the wrapper clearly separate from the Terraform directories while still living in the same repo.

## Minimal viable implementation

The smallest good phase 1 + phase 2 implementation is:

- Python
- Typer
- Pydantic
- PyYAML
- pytest
- subprocess wrappers around `gcloud` and `terraform`

I would avoid adding more complexity unless a specific requirement appears.

## Recommendation

Use a **Python-based `mpc-infra` CLI** with:

- **Typer** for commands
- **Pydantic** for config validation
- **PyYAML** for config files
- **subprocess + JSON parsing** for Terraform and GCP integration
- optional **Rich** for nicer UX later

That is the best balance of:

- low maintenance cost
- rapid iteration
- good operator experience
- future compatibility with upgrade and bootstrap phases
