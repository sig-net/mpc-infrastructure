# Example Node

This folder is a Kubernetes example for the current operator-based
`multichain` runtime.

The resource names are intentionally generic.

The runtime values in the manifests are aligned to the current mainnet VM
deployment contract so the Kubernetes example uses the same network-level
settings.

## Included

- namespace
- Workload Identity service account
- `multichain-node` application deployment
- `multichain-node` load balancer service
- `multichain-node-operator` deployment
- persistent operator release state
- operator RBAC
- Redis master
- Redis replica
- Redis exporter

## Secret Delivery

Secrets should be injected as securely as possible.

Recommended approach:

- use External Secrets Operator (ESO) or an equivalent mechanism
- sync raw secret material into the `multichain-node-secrets` Kubernetes
  `Secret`
- generate the `multichain-node-operator-bootstrap` Kubernetes `Secret`
  from the same secret source plus the non-secret bootstrap values

Two example ESO manifests are included but not referenced by
`kustomization.yaml`:

- `multichain-node-secrets.externalsecret.example.yaml`
- `multichain-node-operator-bootstrap.externalsecret.example.yaml`

If you do not use ESO, please make sure you use a secure secret management solution for kubernetes, kubernetes secrets alone are not sufficent.

## Operator State

The operator records the last applied release in
`/var/lib/chain-signatures/state/agent-state.json`. Keep that path on
persistent storage so a pod restart does not discard its release history. The
example mounts a 1 GiB `ReadWriteOnce` claim at
`/var/lib/chain-signatures/state`.

## GitOps Field Ownership

The release operator updates the node workload's container image, full
environment list, and these pod-template annotations:

- `chain-signatures.sig.network/revision`
- `chain-signatures.sig.network/managed-env-hash`
- `chain-signatures.sig.network/manifest-sha256`

If another controller also reconciles the node workload, configure it to
ignore those fields. Otherwise it can restore the values stored in Git after
the release operator applies a signed release. Continue reconciling the rest
of the workload, including resources, probes, scheduling, services, and RBAC.
