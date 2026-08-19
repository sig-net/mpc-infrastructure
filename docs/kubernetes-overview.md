# Kubernetes Deployment Overview

This repository does not deploy the live Kubernetes environments directly, but
it does define part of the shared release contract those environments are
expected to consume.

For a concrete suggested implementation of the current operator contract, see:

- [kubernetes/README.md](../kubernetes/README.md)
- [kubernetes/chain-signatures/testnet-node-8/README.md](../kubernetes/chain-signatures/testnet-node-8/README.md)

## What Lives Here Versus Elsewhere

This repo owns:

- partner VM Terraform
- operator bootstrap expectations for VM deployments
- the partner-facing naming contract for runtime secrets and manifest bootstrap values

Other repos own:

- signed manifest publishing
- Kubernetes manifests, overlays, and rollout wiring
- cluster-specific secret delivery and workload placement

## Shared Release Model

Both VM-based and Kubernetes-based rollouts are converging on the same core release model:

1. a signed release manifest is published for an environment and channel
2. the bootstrap layer trusts a fixed manifest signing public key
3. the node runtime consumes managed environment values plus bootstrap values
4. the running application is updated according to the selected channel

For VM deployments in this repo, that bootstrap layer is the `chain-signatures-operator` container running beside `multichain` on the host VM.

For Kubernetes deployments, the same concepts apply, but the live cluster-level
implementation lives in the Kubernetes repos:

- the manifest URL and trusted public key need to be injected into the workload bootstrap path
- runtime secrets need to be mounted or injected with names and values that match the expected node contract
- rollout orchestration and reconciliation are handled by cluster-native tooling rather than VM startup scripts

## Runtime Inputs That Must Stay Consistent

Regardless of VM or Kubernetes form factor, the node contract currently includes:

- NEAR account identity and secret key
- cipher key
- sign key
- SK share secret identifier
- Ethereum account key and RPC endpoints
- Solana account key and RPC endpoints
- Hydration connection values where required
- release bootstrap values such as `MANIFEST_URL`, `MANIFEST_CHANNEL`, and the trusted manifest public key

Where Hydration is not active yet, keep the partner-side names and secret wiring in place ahead of time so a later manifest release can enable them without another contract change.

If Kubernetes and VM deployments drift on those names or meanings, a manifest can publish successfully while one environment still fails at runtime. That is why this repo documents the canonical partner-side inputs even though the k8s manifests live elsewhere.

## Practical Guidance

When updating the release contract:

- update the partner Terraform examples here
- update the publisher-managed env references
- update the Kubernetes overlays in the cluster repo
- update migration guidance for already-running partners
- update the suggested manifests in `kubernetes/` when the implementation shape changes

Treat the manifest contract, secret naming, and bootstrap public key as cross-repo changes, not repo-local changes.
