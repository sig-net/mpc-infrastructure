from .constants import PROFILE_DEFAULTS
from .gcloud import validate_gcloud_environment
from .models import PartnerDeploymentConfig, ValidationFinding, ValidationReport


def validate_config_and_environment(config: PartnerDeploymentConfig) -> ValidationReport:
    findings: list[ValidationFinding] = []

    if not config.nodes:
        findings.append(ValidationFinding(level="error", message="At least one node must be defined."))

    defaults = PROFILE_DEFAULTS[config.network_name]
    for idx, node in enumerate(config.nodes):
        if not node.account_id.strip():
            findings.append(ValidationFinding(level="error", message=f"Node {idx} account_id is empty."))
        if defaults["supports_domain"] and not (node.domain and node.domain.strip()):
            findings.append(ValidationFinding(level="error", message=f"Node {idx} domain is required for {config.network_name}."))
        if defaults["supports_hydration"]:
            if not node.secrets.hydration_rpc_ws:
                findings.append(ValidationFinding(level="error", message=f"Node {idx} hydration_rpc_ws is required for {config.network_name}."))
            if not node.secrets.hydration_signer_uri:
                findings.append(ValidationFinding(level="error", message=f"Node {idx} hydration_signer_uri is required for {config.network_name}."))

    findings.extend(validate_gcloud_environment(config))
    ok = not any(f.level == "error" for f in findings)
    return ValidationReport(ok=ok, findings=findings)
