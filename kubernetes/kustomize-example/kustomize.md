# Intent

This section of releases is for partners that want to take more ownership of their node and deploy on GKE or other k8s flavors. Internally we use Kustomize to manage our Mainnet node, Testnet Nodes, and Dev Nodes on Kubernetes. This directory can be treated as a mirror of our current environment, and will be updated on each release to match.

## Pre-requisites

- K8s networking in place, or experience doing so
- Basic understanding of Kustomize
- A K8s cluster managed in whatever flavor you choose
- A way to manage secrets, our example is what we use internally, but there are plenty of other options
- A way to monitor services and ingest logs
- A minimum a Google cloud account that is used to store secrets. (for now)

## What this example is *not*:
- A ready made copy paste solution
- A crash course on Kustomize and Kubernetes
- A recommendation on how to deploy our node
- A budget friendly alternative to VM based nodes

## What this example is:
- A way for Organizations that already utilize K8s to get an idea of resources needed to fit their environment
- Suggestion on how to approach deployments with a wide set of K8s CD management tools (will add new examples, Argo, Helm, etc.)


### High level notes:

1. Secrets management
  - We utilize Google secret manager secrets, and consume them directy from SM with a Helm chart called `kube-secrets-init`. This is an open source tool that works specifically with Google and AWS secrets management and requires a service account to be created in K8s that maps to IAM roles in both GKE and EKS. For GKE, you will have to do Identity Federation in order to authenticate the K8s service account to a Google service account that has secret manager read/write permissions.

  - Another option is to manually create Kubernetes secrets and ingest them into the cluster with one caveat: `MPC_SK_SHARE_SECRET_ID` must be a Google secret as the application itself updates this using a Google SDK. **This is a hard dependancy**. We are working towards a way to have the most secure secrets in a less vendor locked way, however we have trust issues and this is not a simple task to standardize accross many diffent environments.


2. Clustered Redis
  - This is probably overkill for your needs as a single node provider. Where it comes in handy is when you are managing multiple nodes, like we do in our Dev and Testnet environments.

  - Those with a keen eye will notice that redis in this case is not *actually* clustered in our example, and there is a ConfigMap missing in order to do so. We are aware, and for a single node this is fine. If you really want to cluster redis properly, take a look at the Redis documentaion.

  - Monitoring open source Redis will require a 3rd party solution, which I have not given you in this example, as there are many ways to skin a cat here.

  - We are using AOF and persistance in Redis, which is why Redis is a statefulSet in this case, this is **required** for data persistance with triples and presignatures and in case of Redis failures, we can still use the pre-generated triples and presignatures without taxing the network to regenerate those.


3. Certificates & SSL
  - We use GKE internally, and our example reflects this. You will need to figure out your own way to manage certificates if you do not use GKE.

  - An SSL certificate mapped to a domain name is **required** to run a Mainnet node. Testnet has more flexibility, however for Mainnet that contains real assets and money, this is a hard requirement to encrypt internet traffic between nodes.