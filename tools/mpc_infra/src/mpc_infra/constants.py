from pathlib import Path

DEFAULT_NETWORK_NAME = "mainnet"
DEFAULT_REGION = "europe-west1"
DEFAULT_ZONE = "europe-west1-b"
DEFAULT_NETWORK = "default"
DEFAULT_SUBNETWORK = "default"
CONFIG_FILENAME = "partner-deployment.yaml"
GENERATED_TFVARS_FILENAME = "generated.tfvars.json"
REQUIRED_GCP_APIS = [
    "compute.googleapis.com",
    "secretmanager.googleapis.com",
]
REQUIRED_BINARIES = ["gcloud", "terraform", "gh"]
REPO_ROOT = Path(__file__).resolve().parents[4]
TERRAFORM_DIRS = {
    "mainnet": REPO_ROOT / "terraform" / "partner-mainnet",
    "testnet": REPO_ROOT / "terraform" / "partner-testnet",
}
EXAMPLE_TFVARS = {
    "mainnet": TERRAFORM_DIRS["mainnet"] / "terraform-mainnet-example.tfvars",
    "testnet": TERRAFORM_DIRS["testnet"] / "terraform-testnet-example.tfvars",
}
MPC_RELEASE_REPO = "sig-net/mpc"
PROFILE_DEFAULTS = {
    "mainnet": {
        "profile": "mainnet",
        "image": "europe-west1-docker.pkg.dev/near-cs-mainnet/multichain-public/multichain-mainnet:631a0b00085dfc167e115643f791e8eed2cac0cb",
        "image_repository": "europe-west1-docker.pkg.dev/near-cs-mainnet/multichain-public/multichain-mainnet",
        "eth_contract_address": "D39b0aBc0acab7d48aC6DFC9612543f035233b68",
        "sol_program_address": "SigMcRMjKfnC7RDG5q4yUMZM1s5KJ9oYTPP4NmJRDRw",
        "supports_domain": True,
        "supports_hydration": False,
    },
    "testnet": {
        "profile": "testnet",
        "image": "europe-west1-docker.pkg.dev/near-cs-testnet/multichain-public/multichain-testnet:latest",
        "image_repository": "europe-west1-docker.pkg.dev/near-cs-testnet/multichain-public/multichain-testnet",
        "eth_contract_address": "83458E8Bf8206131Fe5c05127007FA164c0948A2",
        "sol_program_address": "SigTVbfRK9LsXWpSv9KgpabrQcFKr5hDdUwMhYsXyKg",
        "supports_domain": False,
        "supports_hydration": True,
    },
}
