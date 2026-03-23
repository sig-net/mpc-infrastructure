from typing import Literal

from pydantic import BaseModel, Field


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
    domain: str
    secrets: SecretRefs


class PartnerMainnetConfig(BaseModel):
    version: Literal[1] = 1
    profile: Literal["mainnet"] = "mainnet"
    project_id: str
    region: str = Field(default="europe-west1")
    zone: str = Field(default="europe-west1-b")
    state_bucket: str
    image: str | None = None
    nodes: list[NodeConfig]


class ValidationFinding(BaseModel):
    level: Literal["info", "warning", "error"]
    message: str


class ValidationReport(BaseModel):
    ok: bool
    findings: list[ValidationFinding]
