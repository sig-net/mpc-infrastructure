from pathlib import Path

from mpc_infra.terraform import plan_changes_summary


def test_plan_changes_summary_includes_source_hint_for_top_level_resource(tmp_path: Path) -> None:
    workdir = tmp_path / "partner-testnet"
    workdir.mkdir()
    (workdir / "main.tf").write_text(
        'resource "google_compute_firewall" "app_port" {\n  name = "x"\n}\n'
    )
    plan_json = {
        "resource_changes": [
            {
                "address": "google_compute_firewall.app_port",
                "change": {"actions": ["update"]},
            }
        ]
    }
    changes = plan_changes_summary(workdir, plan_json)
    assert len(changes) == 1
    assert changes[0].action == "update"
    assert changes[0].source_hint == "main.tf:1"


def test_plan_changes_summary_includes_module_source_hint(tmp_path: Path) -> None:
    workdir = tmp_path / "partner-mainnet"
    modules_dir = tmp_path / "modules" / "instance-from-tpl"
    modules_dir.mkdir(parents=True)
    (workdir).mkdir(exist_ok=True)
    (workdir / "main.tf").write_text(
        'module "instances" {\n  source = "../modules/instance-from-tpl"\n}\n'
    )
    (modules_dir / "main.tf").write_text(
        'resource "google_compute_instance_from_template" "compute_instance" {\n  name = "x"\n}\n'
    )
    plan_json = {
        "resource_changes": [
            {
                "address": "module.instances[0].google_compute_instance_from_template.compute_instance[0]",
                "change": {"actions": ["create"]},
            }
        ]
    }
    changes = plan_changes_summary(workdir, plan_json)
    assert len(changes) == 1
    assert changes[0].action == "create"
    assert changes[0].source_hint == "main.tf:1 -> instance-from-tpl/main.tf:1"
