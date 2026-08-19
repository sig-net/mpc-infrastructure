# Kubernetes Deployment Example

This document is the concise Kubernetes reference for the current operator-based
`multichain` deployment model.

For the concrete manifests, see:

- [kubernetes/chain-signatures/example-node/README.md](../kubernetes/chain-signatures/example-node/README.md)

## Required Components

A Kubernetes-based `multichain` node should include:

- one `multichain-node` workload
- one `multichain-node-operator` workload
- Redis for the node runtime
- operator RBAC so the operator can patch the workload
- a Kubernetes service account for workload identity
- a bootstrap secret for the operator
- an application secret for the runtime values

## Required Runtime Inputs

The Kubernetes deployment should provide the same node contract as the VM
deployment, including:

- NEAR account identity and secret key
- cipher key
- sign key
- SK share secret identifier
- Ethereum account key and RPC endpoints
- Solana account key and RPC endpoints
- Hydration connection values where required
- `MANIFEST_URL`
- `MANIFEST_CHANNEL`
- trusted manifest public key

## Secrets

Secrets should be handled as securely as possible.

Recommended approach:

- use External Secrets Operator (ESO)
- sync the runtime secrets into a Kubernetes `Secret`
- generate the operator bootstrap secret from the same secret source plus the
  non-secret bootstrap values

Do not hardcode secret values in manifests.

## Concrete Example

The example in `kubernetes/chain-signatures/example-node/` includes:

- namespace
- service account
- `multichain-node` deployment
- `multichain-node` load balancer service
- `multichain-node-operator` deployment
- operator RBAC
- Redis master
- Redis replica
- Redis exporter

Use that folder as the concrete reference pattern for Kubernetes-based
`multichain` nodes.
