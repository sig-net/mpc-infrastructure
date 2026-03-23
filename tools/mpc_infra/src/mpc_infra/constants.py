from pathlib import Path

DEFAULT_PROFILE = "mainnet"
DEFAULT_REGION = "europe-west1"
DEFAULT_ZONE = "europe-west1-b"
CONFIG_FILENAME = "partner-mainnet.yaml"
GENERATED_TFVARS_FILENAME = "generated.auto.tfvars.json"
REQUIRED_GCP_APIS = [
    "compute.googleapis.com",
    "secretmanager.googleapis.com",
]
TERRAFORM_PARTNER_MAINNET_DIR = Path(__file__).resolve().parents[4] / "terraform" / "partner-mainnet"
