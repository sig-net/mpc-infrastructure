# Example Node

This folder is a suggested Kubernetes implementation for the operator-based
chain-signatures runtime.

It is intended to answer a practical question that `docs/kubernetes-overview.md`
does not currently answer well enough:

"What do I actually need to deploy for a Kubernetes-based node that matches the
current operator contract?"

The structure mirrors how SIG currently runs these nodes internally, but the
resource names here are intentionally generic.

## Included

- namespace
- Workload Identity service account
- `multichain-node` application deployment
- `multichain-node` load balancer service
- `multichain-node-operator` deployment
- operator RBAC
- Redis master
- Redis replica
- Redis exporter

## Secret Delivery

This example keeps secret delivery deliberately flexible, but the expectation is
still strict: secrets should be injected securely.

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

If you do not use ESO, create equivalent Kubernetes `Secret` objects manually or
with your preferred secret-management workflow.

## Not Included

This example focuses on the node itself and the auxiliary Redis pieces needed by
the node.

It does not include every environment-specific extra from the live testnet
overlay, such as:

- Keel
- Alloy/Grafana wiring
- midnight proof server
- cluster-wide ESO installation and `ClusterSecretStore` setup

Those are environment-level concerns rather than per-node requirements for this
operator migration.
