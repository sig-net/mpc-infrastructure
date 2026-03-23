from typing import Literal

from pydantic import BaseModel, Field


NetworkName = Literal["mainnet", "testnet"]


class SecretRefs(BaseModel):
    account_sk: str
    cipher_sk: str
    sign_sk: str
    sk_share: str
    eth_account_sk: str
    eth_consensus_rpc: str
    eth_execution_rpc: str
    sol_account_sk: str
    sol_rpc_http: str
    sol_rpc_ws: str
    hydration_rpc_ws: str | None = None
    hydration_signer_uri: str | None = None


class NodeConfig(BaseModel):
    account_id: str
    domain: str | None = None
    local_address: str | None = None
    secrets: SecretRefs


class PartnerDeploymentConfig(BaseModel):
    version: Literal[1] = 1
    network_name: NetworkName = "mainnet"
    profile: str
    project_id: str
    region: str = Field(default="europe-west1")
    zone: str = Field(default="europe-west1-b")
    network: str = Field(default="default")
    subnetwork: str = Field(default="default")
    state_bucket: str
    image: str | None = None
    eth_contract_address: str
    sol_program_address: str
    nodes: list[NodeConfig]


class ReleaseSecretRequirement(BaseModel):
    key: str
    secret_name_suggestion: str
    description: str


class ReleaseContract(BaseModel):
    version: str
    image_tag: str
    required_secrets: list[ReleaseSecretRequirement] = []


class StatusReport(BaseModel):
    deployed_version: str
    latest_version: str
    upgrade_available: bool
    missing_secrets: list[str] = []
    recommended_action: str


class ValidationFinding(BaseModel):
    level: Literal["info", "warning", "error"]
    message: str


class ValidationReport(BaseModel):
    ok: bool
    findings: list[ValidationFinding]
