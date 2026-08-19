# Kubernetes Deployment Examples

This folder contains a suggested Kubernetes implementation for the operator-based
chain-signatures deployment model introduced in this repository.

The current concrete example is:

- `chain-signatures/testnet-node-8/`

That example mirrors the live testnet node 8 rollout shape in `sig-kustomize`
closely enough to show the required moving parts for this change:

- the `multichain` workload
- the separate `chain-signatures-operator` workload
- the operator bootstrap contract
- the RBAC needed for the operator to patch the workload
- the GKE Workload Identity service account pattern
- Redis master, Redis replica, and Redis exporter
- a per-node `LoadBalancer` service

This example intentionally does not commit raw secrets.

Secret injection should be done as securely as possible. Prefer External Secrets
Operator (ESO) or an equivalent cluster-native secret delivery mechanism over
hardcoding secrets in manifests. Example ESO manifests are included in the
example folder, but they are not wired into the deployable `kustomization.yaml`
until you customize them for your cluster.

This folder is a suggested implementation, not the source of truth for the live
cluster. If the live `sig-kustomize` overlays evolve, keep these examples in
sync with the release contract documented here.
