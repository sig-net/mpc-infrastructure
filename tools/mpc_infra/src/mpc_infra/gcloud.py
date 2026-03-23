from .models import ValidationFinding


def validate_gcloud_environment(project_id: str) -> list[ValidationFinding]:
    # Placeholder for phase-4 implementation.
    return [
        ValidationFinding(
            level="info",
            message=f"gcloud validation for project {project_id} is not implemented yet.",
        )
    ]


def create_secret_interactively(project_id: str, secret_name: str, description: str) -> ValidationFinding:
    # Placeholder for guided Secret Manager creation during upgrade.
    return ValidationFinding(
        level="info",
        message=(
            f"Secret creation flow for {secret_name} in project {project_id} is not implemented yet "
            f"({description})."
        ),
    )
