from .gcloud import validate_gcloud_environment
from .models import ValidationFinding, ValidationReport


def validate_config_and_environment(project_id: str) -> ValidationReport:
    findings: list[ValidationFinding] = []
    findings.extend(validate_gcloud_environment(project_id))
    ok = not any(f.level == "error" for f in findings)
    return ValidationReport(ok=ok, findings=findings)
