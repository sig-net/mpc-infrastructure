# Migration Guide For Existing Partner Nodes

This guide is for partners who already run an older Multichain deployment and need to move to the current operator-based contract without treating the node as a brand new install.

Use this guide when the partner already has:

- an existing GCP project
- an existing VM-based node
- existing Secret Manager entries
- an existing DNS name or load balancer

## What Changed In The New Deployment Model

The current contract adds or formalizes several things that older partner deployments may not have had:

- a `chain-signatures-operator` container running beside the application container
- signed release manifest bootstrap via `manifest_url`, `manifest_channel`, and `trusted_manifest_pubkey`
- stricter alignment between Terraform secret names and runtime secret references
- explicit Solana and Hydration runtime inputs in the mainnet contract

In other words, the migration is not just “change the app image.” It is a bootstrap-contract migration.

## Before You Touch Terraform

Inventory the current deployment first.

Confirm:

- which branch or revision of this repo last drove the partner deployment
- the current app image on the VM
- whether an operator container already exists
- the current Secret Manager secret names in the partner project
- whether the node already has the Hydration values available
- the current DNS name and load balancer setup

Do not assume the current live secret names match the current example tfvars. Check them.

## Minimum Migration Prerequisites

Before applying the new config, make sure you have:

- the approved current `image`
- the approved current `operator_image`
- the correct `manifest_url`
- the correct `trusted_manifest_pubkey`
- all required current Secret Manager secret IDs populated

Those release values are already supplied in the Terraform code for the current contract, so partners should verify that their deployment values match what is on the current `main` branch instead of copying them from older rollout notes.

For mainnet, that means the deployment should be able to resolve:

- `multichain-account-sk-mainnet-0`
- `multichain-cipher-sk-mainnet-0`
- `multichain-sign-sk-mainnet-0`
- `multichain-sk-share-mainnet-0`
- `multichain-eth-account-sk-mainnet-0`
- `multichain-eth-consensus-rpc-url-mainnet`
- `multichain-eth-execution-rpc-url-mainnet`
- `multichain-sol-account-sk-mainnet-0`
- `multichain-sol-rpc-ws-url-mainnet`
- `multichain-sol-rpc-http-url-mainnet`
- `multichain-hydration-rpc-ws-url-mainnet`
- `multichain-hydration-signer-uri-mainnet`

## Secret Strategy

For existing partners, the safest migration pattern is:

1. keep the live secret values
2. create any missing canonical secret IDs as duplicates first
3. update Terraform and publisher references to the canonical names
4. migrate away from legacy or ad hoc names only after the new deployment is confirmed healthy

This avoids turning a naming cleanup into an outage.

If a partner currently uses older names, do not rename by deleting first. Duplicate first, validate, then clean up later.

## Terraform Changes To Expect

Compared with older deployments, expect to add or confirm:

- `operator_image`
- `manifest_url`
- `trusted_manifest_pubkey`
- `manifest_channel`
- `poll_interval_seconds` if you need a non-default setting
- Solana secret IDs
- Hydration secret IDs for mainnet, or Hydration values for testnet

Review:

- `terraform/partner-mainnet/terraform-mainnet-example.auto.tfvars`
- `terraform/partner-testnet/terraform-testnet-example.auto.tfvars`

against the current live state instead of blindly copying over them.

For Hydration, note that the not-yet-shipped portion of the migration currently uses temporary placeholder values of `"1"`. Call that out explicitly so nobody mistakes the placeholder for a missing production secret.

## Migration Sequence

### Option A: in-place migration on the existing node

Use this for current partner-node migrations. The migrated node keeps the same identity as the existing deployment, so this is the only supported option for now.

Recommended order:

1. duplicate missing secrets to the canonical IDs
2. update tfvars to the current contract
3. run `terraform plan`
4. confirm the plan does not unintentionally replace networking or identity resources you meant to keep
5. apply
6. verify that both `multichain` and `chain-signatures-operator` are running
7. confirm the operator can read and apply the signed manifest

## Post-Migration Validation

After apply, verify:

- the operator container is running
- the app container is running
- the bootstrap files exist under `/var/lib/chain-signatures`
- the operator logs show successful manifest verification
- the published channel manifest being consumed matches the intended environment
- no secrets are missing at startup

Useful host checks:

```bash
docker ps
docker logs chain-signatures-operator
docker logs multichain
sudo ls -R /var/lib/chain-signatures
```

## Common Migration Risks

- secret names in Terraform do not exist in Secret Manager
- legacy secret names still exist, but the new canonical names do not
- Hydration values were never provisioned for the older deployment
- DNS is pointed correctly, but the load balancer backend is unhealthy
- the operator bootstrap key or manifest URL is wrong for the environment

The migration should be treated as successful only after the operator has reconciled the workload against the signed manifest, not merely after Terraform apply succeeds.
