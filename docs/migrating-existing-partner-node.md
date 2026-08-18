# Migration Guide For Existing Partner Nodes

This guide is for partners who already run an older Multichain deployment and need to move to the current operator-based contract without treating the node as a brand new install.

Use this guide when the partner already has:

- an existing GCP project
- an existing VM-based node
- existing Secret Manager entries
- an existing DNS name or load balancer

Use the new-partner bootstrap guide instead when you are building a fresh node:

- [Partner VM Bootstrap Guide](partner-vm-bootstrap.md)

## What Changed In The New Deployment Model

The current contract adds or formalizes several things that older partner deployments may not have had:

- a `chain-signatures-operator` container running beside the application container
- signed release manifest bootstrap via `manifest_url`, `manifest_channel`, and `trusted_manifest_pubkey`
- stricter alignment between Terraform secret names and runtime secret references
- explicit Solana and Hydration runtime inputs in the mainnet contract

In other words, the migration is not just “change the app image.” It is a bootstrap-contract migration.

## Migration Requirements

Before starting, make sure you have:

- admin access to the existing GCP project
- permission to read Secret Manager metadata and current secret values or
  versions
- permission to inspect or update the existing VM, load balancer, and DNS
  configuration
- a local machine with `git`, `gcloud`, and `terraform`
- access to the chain-signatures team for current release values if your old
  rollout notes are stale
- the approved current `image`
- the approved current `operator_image`
- the correct `manifest_url`
- the correct `trusted_manifest_pubkey`
- all required current Secret Manager secret IDs populated

Those release values are already supplied in the Terraform code for the current
contract, so partners should verify that their deployment values match what is
on the current `main` branch instead of copying them from older rollout notes.

## If The Original Owners Changed

For older partner deployments, do not assume the same people still own the GCP
project, DNS zone, Terraform state bucket, or Secret Manager entries.

Before touching infrastructure, confirm who currently controls:

- the GCP project that hosts the node
- the Terraform state bucket and state path
- the DNS zone or registrar account
- the NEAR account tied to the node
- the Secret Manager secrets currently used by production
- any existing runbooks or rollout notes

If some of that ownership is unclear, stop and resolve that first. Migration is
hard to recover cleanly if you discover halfway through that the team cannot
update DNS, inspect the old VM, or read the production secret set.

## Inventory The Current Deployment

Inventory the live deployment before writing or changing tfvars.

Confirm:

- which branch or revision of this repo last drove the partner deployment
- the current app image on the VM
- whether an operator container already exists
- the current Secret Manager secret names in the partner project
- whether the node already has the Hydration values available
- the current DNS name and load balancer setup
- the current service account attached to the VM
- the existing Terraform state location if Terraform still manages the node
- whether any handwritten startup-script or metadata changes were applied outside
  Terraform

Do not assume the current live secret names match the current example tfvars. Check them.

Useful checks:

```bash
gcloud config set project <your-project-id>
gcloud compute instances list --project <your-project-id>
gcloud secrets list --project <your-project-id>
gcloud compute forwarding-rules list --project <your-project-id>
gcloud compute backend-services list --project <your-project-id>
```

You should also log into the existing host and capture the current runtime
shape:

```bash
docker ps
docker logs chain-signatures-operator
docker logs multichain
sudo ls -R /var/lib/chain-signatures
```

## Canonical Secret IDs

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

For the Hydration mainnet secrets, the goal is to have the canonical secret IDs created and wired now even before Hydration is enabled in the live manifest. Keep placeholder current values or revisions in place for now, then add a new secret revision later when the signed manifest release is ready to consume them.

For testnet, the deployment should be able to resolve:

- `multichain-account-sk-testnet-0`
- `multichain-cipher-sk-testnet-0`
- `multichain-sign-sk-testnet-0`
- `multichain-sk-share-testnet-0`
- `multichain-eth-account-sk-testnet-0`
- `multichain-eth-consensus-rpc-url-testnet`
- `multichain-eth-execution-rpc-url-testnet`
- `multichain-sol-account-sk-testnet-0`
- `multichain-sol-rpc-http-url-testnet`
- `multichain-sol-rpc-ws-url-testnet`

The current testnet module also depends on:

- `multichain-indexer-aws-access-key`
- `multichain-indexer-aws-secret-key`

## Secret Strategy

For existing partners, the safest migration pattern is:

1. keep the live secret values
2. create any missing canonical secret IDs as duplicates first
3. update Terraform and publisher references to the canonical names
4. migrate away from legacy or ad hoc names only after the new deployment is confirmed healthy

This avoids turning a naming cleanup into an outage.

If a partner currently uses older names, do not rename by deleting first. Duplicate first, validate, then clean up later.

If the partner has secrets but no longer knows which ones are actually live,
capture the current VM environment and map each live value back to its Secret
Manager source before changing names or versions.

## Prepare Local Tooling

Authenticate `gcloud` and make sure Terraform can read the existing project:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project <your-project-id>
gcloud auth application-default set-quota-project <your-project-id>
```

## Terraform Changes To Expect

Compared with older deployments, expect to add or confirm:

- `operator_image`
- `manifest_url`
- `trusted_manifest_pubkey`
- `manifest_channel`
- `poll_interval_seconds` if you need a non-default setting
- Solana secret IDs
- Hydration secret IDs for mainnet, or Hydration values for testnet

Review the environment-specific tfvars file that matches the deployment you are
migrating:

- `terraform/partner-mainnet/terraform-mainnet-example.auto.tfvars`
- `terraform/partner-testnet/terraform-testnet-example.auto.tfvars`

Use those files as the source of truth for which inputs belong to mainnet vs
testnet, then compare them against the current live state instead of blindly
copying over them.

Migration tfvars should preserve existing identity and routing values unless you
intend to rotate them. In practice, verify especially:

- `project_id`
- `network` and `subnetwork`
- `region` and `zone`
- `node_configs[*].account`
- the existing mainnet domain or existing testnet endpoint
- the secret IDs currently used by production
- the current contract addresses or program addresses already tied to the node

For Hydration, call out explicitly that these secrets are staged but not active
yet. Partners should create the canonical secret IDs now, use placeholder
current values or revisions for the time being, and expect a later
signed-manifest release to start consuming them.

## Migration Sequence

For current partner-node migrations, keep the existing node identity and update
it in place.

Recommended order:

1. duplicate missing secrets to the repo’s expected secret IDs for that environment
2. update the matching tfvars file to the current contract
3. run `terraform plan` from the correct Terraform directory
4. confirm the plan does not unintentionally replace networking, DNS-facing, or identity resources you meant to keep
5. run `terraform apply`
6. verify that both `multichain` and `chain-signatures-operator` are running
7. confirm the operator can read and apply the signed manifest

In step 1, “repo’s expected secret IDs” means the exact secret names used by the
current Terraform contract in this repository for the target environment. Use:

- `terraform/partner-mainnet/terraform-mainnet-example.auto.tfvars` for mainnet
- `terraform/partner-testnet/terraform-testnet-example.auto.tfvars` for testnet

If the live project still uses older names, duplicate the current secret values
to the names shown in the matching file before changing Terraform inputs.

In step 2, edit the file that matches the environment you are migrating:

- mainnet: `terraform/partner-mainnet/terraform-mainnet.auto.tfvars`
- testnet: `terraform/partner-testnet/terraform-testnet.auto.tfvars`

If you do not already have a local env-specific tfvars file, start by copying
from the matching example file in the same directory and then replace the values
with the current live deployment values.

In steps 3 through 5, run Terraform from the environment directory you are
migrating:

For mainnet:

```bash
cd terraform/partner-mainnet
terraform init
terraform plan -var-file=terraform-mainnet.auto.tfvars
terraform apply -var-file=terraform-mainnet.auto.tfvars
```

For testnet:

```bash
cd terraform/partner-testnet
terraform init
terraform plan -var-file=terraform-testnet.auto.tfvars
terraform apply -var-file=terraform-testnet.auto.tfvars
```

In steps 6 and 7, operators should verify the runtime directly on the host:

```bash
docker ps
docker logs chain-signatures-operator
docker logs multichain
sudo ls -R /var/lib/chain-signatures
```

They should see both containers running, no missing-secret errors, and operator
logs that show successful signed-manifest verification and reconcile behavior
for the intended environment and channel.

During plan review, pay particular attention to any proposed replacement of:

- service accounts
- reserved IP addresses
- managed SSL certificates
- forwarding rules
- backend services
- DNS-facing hostnames

If Terraform wants to replace one of those unexpectedly, stop and reconcile the
inputs before apply.

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

Recommended external checks:

```bash
gcloud compute instances list --project <your-project-id>
gcloud compute backend-services get-health <backend-service-name> --global --project <your-project-id>
curl -I https://<hostname>
```

## Common Migration Risks

- secret names in Terraform do not exist in Secret Manager
- legacy secret names still exist, but the new canonical names do not
- Hydration secret IDs were never provisioned for the older deployment, even though a later manifest release will expect them
- DNS is pointed correctly, but the load balancer backend is unhealthy
- the operator bootstrap key or manifest URL is wrong for the environment
- the current team can read the project but cannot update DNS or the Terraform state
- handwritten changes on the old VM are silently lost because they were never captured in Terraform inputs

The migration should be treated as successful only after the operator has reconciled the workload against the signed manifest, not merely after Terraform apply succeeds.
