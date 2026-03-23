from mpc_infra.upgrade import status_against_latest_release


def test_status_report_has_recommended_action() -> None:
    report = status_against_latest_release()
    assert report.latest_version
    assert report.recommended_action
