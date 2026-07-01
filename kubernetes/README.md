# Kubernetes Deployment Examples

This folder holds generic Kubernetes resource examples for operators who want
to run multichain on their own cluster.

The intent is to document a deployment model, not to impose a delivery tool.
These manifests are plain YAML so teams can apply them with whatever workflow
they already use:

- `kubectl`
- GitOps
- Helm wrappers
- internal CD pipelines

## Design Goals

- keep the example repo-native and easy to audit
- avoid assuming Flux, Argo CD, Helm, or any other specific controller
- separate non-secret environment from secret material
- show one-node examples that operators can duplicate or templatize for larger fleets
- stay compatible with digest-pinned image promotion managed outside this repo

## Layout

- `partner-mainnet/`
- `partner-testnet/`

Each environment folder contains:

- `example-node.yaml`: namespace, service account, services, config maps, multichain workload, and operator deployment
- `secret.example.yaml`: placeholder secret values that should be replaced by the operator's secret workflow

The example workload uses a single-replica `StatefulSet` with a headless
`Service` so the node gets a stable DNS identity that can be wired into
`MPC_LOCAL_ADDRESS`.

The resource names are intentionally kept short around the pattern
`multichain-<environment>` so operators can templatize them without carrying
extra naming noise from this repo.

## What These Examples Assume

- operators already have a Kubernetes cluster
- operators already have a way to deliver container images to that cluster
- operators can supply secret values through Kubernetes Secrets or their own secret sync mechanism
- Redis is provided either in-cluster or as an external endpoint reachable from the workload

## What These Examples Do Not Assume

- any particular GitOps or CD tool
- any specific ingress controller or load balancer product
- any specific secret manager integration

These examples pin the multichain workload image directly in the pod spec. If
an operator later wants to layer in signed manifest promotion for Kubernetes,
they can keep the same resource shape and swap only the image/env delivery path.

## Adapting The Examples

Most operators will need to adjust at least:

- namespace names
- image digests
- service account annotations
- resource requests and limits
- `MPC_LOCAL_ADDRESS`
- `MPC_REDIS_URL`
- manifest URL and trust root values
- secret delivery
- external service exposure for HTTP or peer traffic

The `secret.example.yaml` files are intentionally not ready to apply as-is.
They are templates showing which keys need to exist.
