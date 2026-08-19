# Example Node

This folder is a concrete Kubernetes example for the current operator-based
`multichain` runtime.

The resource names are intentionally generic.

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

If you do not use ESO, create equivalent Kubernetes `Secret` objects manually or
with your preferred secret-management workflow.
