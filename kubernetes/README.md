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
- show one-node examples that operators can duplicate or templatize for larger fleets
- stay compatible with digest-pinned image promotion managed outside this repo
- mirror the current mainnet workload split closely enough that operators can reason from the live shape

## Layout

- `partner-mainnet/`
- `partner-testnet/`

Each environment folder contains:

- `example-node.yaml`: namespace, service account, RBAC, Redis, multichain workload, and operator deployment

The resource names are intentionally kept short around the pattern
`multichain-<environment>` so operators can templatize them without carrying
extra naming noise from this repo.

## What These Examples Assume

- operators already have a Kubernetes cluster
- operators already have a way to deliver container images to that cluster
- operators have a secure way to inject sensitive values into workloads
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
- service account annotations or identity bindings
- resource requests and limits
- `MPC_LOCAL_ADDRESS`
- `MPC_REDIS_URL`
- manifest URL and trust root values
- secret injection method for sensitive values
- external service exposure for HTTP or peer traffic
