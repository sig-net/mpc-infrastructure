provider "google" {
  project = var.project_id
}
provider "google-beta" {
  project = var.project_id
}

locals {
  deployment_node = var.node_configs[0]
  deployment_name = "multichain-${var.env}-${local.deployment_node.node_id}"
}

resource "google_compute_project_metadata_item" "project_logging" {
  key   = "google-logging-enabled"
  value = "true"
}

resource "google_service_account" "service_account" {
  account_id   = local.deployment_name
  display_name = "Multichain ${var.env} Node ${local.deployment_node.node_id}"
}

resource "google_project_iam_member" "sa-roles" {
  for_each = toset([
    "roles/secretmanager.admin",
    "roles/storage.objectAdmin",
    "roles/iam.serviceAccountAdmin",
    "roles/logging.logWriter",
  ])

  role    = each.key
  member  = "serviceAccount:${google_service_account.service_account.email}"
  project = var.project_id
}

resource "google_compute_global_address" "external_ips" {
  count        = length(var.node_configs)
  name         = local.deployment_name
  address_type = "EXTERNAL"
}

module "ig_template" {
  count  = length(var.node_configs)
  source = "../modules/mig_template"

  network    = var.network
  subnetwork = var.subnetwork
  region     = var.region

  service_account = {
    email  = google_service_account.service_account.email
    scopes = ["cloud-platform"]
  }

  name_prefix  = "${local.deployment_name}-"
  machine_type = "n2d-standard-2"

  startup_script = templatefile("${path.module}/scripts/startup.sh.tftpl", {
    image                = var.image
    operator_image       = var.operator_image
    image_port           = var.image_port
    bootstrap_static_env = [for item in var.static_env : item if contains(["MPC_WEB_PORT"], item.name)]
    managed_env = merge(
      { for item in var.static_env : item.name => item.value if !contains(["MPC_WEB_PORT"], item.name) },
      {
        MPC_ACCOUNT_SK                 = data.google_secret_manager_secret_version.account_sk_secret_id[count.index].secret_data
        MPC_CIPHER_SK                  = data.google_secret_manager_secret_version.cipher_sk_secret_id[count.index].secret_data
        MPC_SIGN_SK                    = data.google_secret_manager_secret_version.sign_sk_secret_id[count.index].secret_data
        AWS_ACCESS_KEY_ID              = data.google_secret_manager_secret_version.aws_access_key_secret_id.secret_data
        AWS_SECRET_ACCESS_KEY          = data.google_secret_manager_secret_version.aws_secret_key_secret_id.secret_data
        MPC_SK_SHARE_SECRET_ID         = var.node_configs[count.index].sk_share_secret_id
        MPC_REDIS_URL                  = var.redis_url
        MPC_ETH_ACCOUNT_SK             = data.google_secret_manager_secret_version.eth_account_sk_secret_id[count.index].secret_data
        MPC_ETH_CONSENSUS_RPC_HTTP_URL = data.google_secret_manager_secret_version.eth_consensus_rpc_url_secret_id[count.index].secret_data
        MPC_ETH_EXECUTION_RPC_HTTP_URL = data.google_secret_manager_secret_version.eth_execution_rpc_url_secret_id[count.index].secret_data
        MPC_ETH_CONTRACT_ADDRESS       = var.node_configs[count.index].eth_contract_address
        MPC_SOL_ACCOUNT_SK             = data.google_secret_manager_secret_version.sol_account_sk_secret_id[count.index].secret_data
        MPC_SOL_RPC_HTTP_URL           = data.google_secret_manager_secret_version.sol_rpc_http_url_secret_id[count.index].secret_data
        MPC_SOL_RPC_WS_URL             = data.google_secret_manager_secret_version.sol_rpc_ws_url_secret_id[count.index].secret_data
        MPC_SOL_PROGRAM_ADDRESS        = var.node_configs[count.index].sol_program_address
        MPC_HYDRATION_RPC_WS_URL       = var.node_configs[count.index].hydration_rpc_ws_url
        MPC_HYDRATION_SIGNER_URI       = var.node_configs[count.index].hydration_signer_uri
      }
    )
    participant_name        = local.deployment_name
    node_id                 = var.node_configs[count.index].node_id
    project_id              = var.project_id
    manifest_url            = var.manifest_url
    manifest_channel        = var.manifest_channel
    trusted_manifest_pubkey = var.trusted_manifest_pubkey
    account_id              = var.node_configs[count.index].account
    local_address           = "http://${google_compute_global_address.external_ips[count.index].address}"
    env_name                = var.env
    poll_interval_seconds   = var.poll_interval_seconds
  })

  source_image = var.source_image
  metadata     = var.additional_metadata

  tags = [
    "multichain",
    "allow-ssh"
  ]

  labels = {}

  depends_on = [google_compute_global_address.external_ips]
}


module "instances" {
  count      = length(var.node_configs)
  source     = "../modules/instance-from-tpl"
  region     = var.region
  project_id = var.project_id
  hostname   = local.deployment_name
  network    = var.network
  subnetwork = var.subnetwork

  instance_template = module.ig_template[count.index].self_link_unique

}

resource "google_compute_health_check" "multichain_healthcheck" {
  name = "${local.deployment_name}-healthcheck"

  http_health_check {
    port         = 3000
    request_path = "/"
  }

}

resource "google_compute_global_forwarding_rule" "default" {
  count                 = length(var.node_configs)
  name                  = "${local.deployment_name}-rule"
  target                = google_compute_target_http_proxy.default[count.index].id
  port_range            = "80"
  load_balancing_scheme = "EXTERNAL"
  ip_address            = google_compute_global_address.external_ips[count.index].address
}

resource "google_compute_target_http_proxy" "default" {
  count       = length(var.node_configs)
  name        = "${local.deployment_name}-target-proxy"
  description = "a description"
  url_map     = google_compute_url_map.default[count.index].id
}

resource "google_compute_url_map" "default" {
  count           = length(var.node_configs)
  name            = "${local.deployment_name}-url-map"
  default_service = google_compute_backend_service.multichain_backend.id
}

resource "google_compute_backend_service" "multichain_backend" {
  name                  = "${local.deployment_name}-backend-service"
  load_balancing_scheme = "EXTERNAL"

  backend {
    group = google_compute_instance_group.multichain_group.id
  }

  health_checks = [google_compute_health_check.multichain_healthcheck.id]
}

resource "google_compute_instance_group" "multichain_group" {
  name      = "${local.deployment_name}-instance-group"
  instances = module.instances[*].self_links[0]

  zone = var.zone
  named_port {
    name = "http"
    port = 3000
  }
}

resource "google_compute_firewall" "app_port" {
  name    = "allow-${local.deployment_name}-healthcheck-access"
  network = var.network

  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  source_tags   = ["multichain"]

  allow {
    protocol = "tcp"
    ports    = ["80", "3000"]
  }

}
