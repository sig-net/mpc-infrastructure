# Kubernetes Manifests

This folder contains a concrete Kubernetes example for the current operator-based
`multichain` deployment model.

Use:

- `chain-signatures/example-node/`

The example includes the `multichain` workload, the separate operator workload,
Redis, the required RBAC, and example ESO-based secret delivery.

Secrets should be handled as securely as possible. The recommended approach is
External Secrets Operator (ESO), which is why the example includes ESO manifests
for the application secret and operator bootstrap secret.
