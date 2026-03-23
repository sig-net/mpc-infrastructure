from .gcloud import validate_gcloud_environment
from .models import PartnerMainnetConfig, ValidationFinding, ValidationReport


def validate_config_and_environment(config: PartnerMainnetConfig) -> ValidationReport:
    findings: list[ValidationFinding] = []

    if not config.nodes:
        findings.append(ValidationFinding(level="error", message="At least one node must be defined."))

    for idx, node in enumerate(config.nodes):
        if not node.account_id.strip():
            findings.append(ValidationFinding(level="error", message=f"Node {idx} account_id is empty."))
        if not node.domain.strip():
            findings.append(ValidationFinding(level="error", message=f"Node {idx} domain is empty."))

    findings.extend(validate_gcloud_environment(config))
    ok = not any(f.level == "error" for f in findings)
    return ValidationReport(ok=ok, findings=findings)
