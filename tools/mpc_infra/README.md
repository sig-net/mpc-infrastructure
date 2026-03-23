# mpc-infra

`mpc-infra` is a proposed wrapper CLI for partner mainnet deployment workflows in `sig-net/mpc-infrastructure`.

Planned commands:

- `mpc-infra init`
- `mpc-infra validate`
- `mpc-infra plan`
- `mpc-infra deploy`
- `mpc-infra status`
- `mpc-infra upgrade`

The upgrade path is intended to evolve into a release migration assistant that can:

- detect newly required env/secret requirements from release metadata
- prompt the operator for missing secret values
- create missing GCP Secret Manager secrets before rollout

This initial scaffold is intentionally light and exists to make the repo layout and implementation path concrete.
