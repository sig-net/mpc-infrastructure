from .models import ValidationFinding


def validate_gcloud_environment(project_id: str) -> list[ValidationFinding]:
    # Placeholder for phase-4 implementation.
    return [
        ValidationFinding(
            level="info",
            message=f"gcloud validation for project {project_id} is not implemented yet.",
        )
    ]
