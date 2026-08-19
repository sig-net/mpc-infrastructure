# Multichain Infrastructure

This repository is the source of truth for partner-owned Multichain node
infrastructure and the partner-facing runtime contract around those nodes.

At a high level, this repo contains:

- Terraform for partner VM deployments on GCP
- the VM bootstrap contract used by the operator-based deployment model
- supporting docs for new partner installs, migrations, and release-model
  context

The detailed deployment model, runtime scope, and secret/bootstrap contract now
live in [docs/repository-overview.md](docs/repository-overview.md).

## Repo Layout

- `terraform/partner-mainnet` - current mainnet partner VM deployment
- `terraform/partner-testnet` - current testnet partner VM deployment
- `terraform/modules/instance-from-tpl` - VM instantiation helper
- `terraform/modules/mig_template` - COS instance-template helper
- `terraform/modules/multichain` - older Cloud Run deployment module
- `key_scripts/generate_keys` - helper for generating bootstrap keys
- `docs/` - deployment, migration, and repository reference docs

## Docs Directory

- [Repository Overview](docs/repository-overview.md) - what this repo owns,
  deployment models, current scope, and runtime contract
- [Partner VM Bootstrap Guide](docs/partner-vm-bootstrap.md) - step-by-step
  guide for a new partner VM deployment
- [Migration Guide For Existing Partner Nodes](docs/migrating-existing-partner-node.md) -
  moving an existing partner deployment onto the current operator-based contract
- [Kubernetes Deployment Overview](kubernetes/chain-signatures/example-node/README.md) - how the
  shared signed-release model relates to Kubernetes deployments outside this repo

## Recommended Reading Order

If you are deploying a brand new partner node:

1. [Repository Overview](docs/repository-overview.md)
2. [Partner VM Bootstrap Guide](docs/partner-vm-bootstrap.md)
3. Review the appropriate example tfvars:
   - `terraform/partner-mainnet/terraform-mainnet-example.auto.tfvars`
   - `terraform/partner-testnet/terraform-testnet-example.auto.tfvars`
4. Populate Secret Manager with the expected secret names
5. Run Terraform
6. Complete DNS cutover and validation

If you already run an older partner deployment:

- [Migration Guide For Existing Partner Nodes](docs/migrating-existing-partner-node.md)
