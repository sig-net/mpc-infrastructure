from pathlib import Path

DEFAULT_PROFILE = "mainnet"
DEFAULT_REGION = "europe-west1"
DEFAULT_ZONE = "europe-west1-b"
DEFAULT_NETWORK = "default"
DEFAULT_SUBNETWORK = "default"
DEFAULT_IMAGE = (
    "europe-west1-docker.pkg.dev/near-cs-mainnet/"
    "multichain-public/multichain-mainnet:631a0b00085dfc167e115643f791e8eed2cac0cb"
)
DEFAULT_ETH_CONTRACT_ADDRESS = "D39b0aBc0acab7d48aC6DFC9612543f035233b68"
DEFAULT_SOL_PROGRAM_ADDRESS = "SigMcRMjKfnC7RDG5q4yUMZM1s5KJ9oYTPP4NmJRDRw"
CONFIG_FILENAME = "partner-mainnet.yaml"
GENERATED_TFVARS_FILENAME = "generated.auto.tfvars.json"
REQUIRED_GCP_APIS = [
    "compute.googleapis.com",
    "secretmanager.googleapis.com",
]
REQUIRED_BINARIES = ["gcloud", "terraform"]
TERRAFORM_PARTNER_MAINNET_DIR = Path(__file__).resolve().parents[4] / "terraform" / "partner-mainnet"
