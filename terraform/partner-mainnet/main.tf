provider "google" {
  project = var.project_id
}
provider "google-beta" {
  project = var.project_id
}

resource "google_compute_project_metadata_item" "project_logging" {
  key   = "google-logging-enabled"
  value = "true"
}


resource "google_service_account" "service_account" {
  account_id   = "multichain-partner-${var.env}"
  display_name = "Multichain ${var.env} Account"
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
  name         = "multichain-partner-mainnet-${count.index}"
  address_type = "EXTERNAL"

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_compute_managed_ssl_certificate" "mainnet_ssl" {
  count = length(var.node_configs)
  name  = "multichain-partner-mainnet-ssl-${count.index}"

  managed {
    domains = [var.node_configs[count.index].domain]
  }
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

  name_prefix  = "multichain-partner-mainnet-${count.index}"
  machine_type = "n2d-standard-4"

  startup_script = templatefile("${path.module}/scripts/startup.sh.tftpl", {
    image                        = var.image
    image_port                   = var.image_port
    static_env                   = var.static_env
    node_id                      = count.index
    project_id                   = var.project_id
    account_id                   = var.node_configs[count.index].account
    account_sk                   = data.google_secret_manager_secret_version.account_sk_secret_id[count.index].secret_data
    cipher_sk                    = data.google_secret_manager_secret_version.cipher_sk_secret_id[count.index].secret_data
    sign_sk                      = data.google_secret_manager_secret_version.sign_sk_secret_id[count.index] != null ? data.google_secret_manager_secret_version.sign_sk_secret_id[count.index].secret_data : data.google_secret_manager_secret_version.account_sk_secret_id[count.index].secret_data
    aws_access_key_id            = "1"
    aws_secret_access_key        = "1"
    local_address                = "https://${var.node_configs[count.index].domain}"
    sk_share_secret_id           = var.node_configs[count.index].sk_share_secret_id
    env_name                     = var.env
    redis_url                    = var.redis_url
    eth_account_sk               = data.google_secret_manager_secret_version.eth_account_sk_secret_id[count.index].secret_data
    eth_consensus_rpc_http_url   = data.google_secret_manager_secret_version.eth_consensus_rpc_url_secret_id[count.index].secret_data
    eth_execution_rpc_http_url   = data.google_secret_manager_secret_version.eth_execution_rpc_url_secret_id[count.index].secret_data
    eth_contract_address         = var.node_configs[count.index].eth_contract_address
    sol_account_sk               = data.google_secret_manager_secret_version.sol_account_sk_secret_id[count.index].secret_data
    sol_rpc_http_url             = data.google_secret_manager_secret_version.sol_rpc_http_url_secret_id[count.index].secret_data
    sol_rpc_ws_url               = data.google_secret_manager_secret_version.sol_rpc_ws_url_secret_id[count.index].secret_data
    sol_program_address          = var.node_configs[count.index].sol_program_address
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
  hostname   = "multichain-mainnet-partner-${count.index}"
  network    = var.network
  subnetwork = var.subnetwork

  instance_template = module.ig_template[count.index].self_link_unique

}

resource "google_compute_health_check" "multichain_healthcheck" {
  name = "multichain-mainnet-partner-healthcheck"

  http_health_check {
    port         = 3000
    request_path = "/"
  }

}

resource "google_compute_global_forwarding_rule" "http_fw" {
  count                 = length(var.node_configs)
  name                  = "multichain-partner-mainnet-http-rule-${count.index}"
  target                = google_compute_target_http_proxy.default[count.index].id
  port_range            = "80"
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL"
  ip_address            = google_compute_global_address.external_ips[count.index].address
}

resource "google_compute_global_forwarding_rule" "https_fw" {
  count                 = length(var.node_configs)
  name                  = "multichain-partner-mainnet-https-rule-${count.index}"
  target                = google_compute_target_https_proxy.default_https[count.index].id
  port_range            = "443"
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL"
  ip_address            = google_compute_global_address.external_ips[count.index].address
}

resource "google_compute_target_http_proxy" "default" {
  count       = length(var.node_configs)
  name        = "multichain-partner-mainnet-http-target-proxy-${count.index}"
  description = "a description"
  url_map     = google_compute_url_map.redirect_default[count.index].id
}

resource "google_compute_target_https_proxy" "default_https" {
  count            = length(var.node_configs)
  name             = "multichain-partner-mainnet-https-target-proxy-${count.index}"
  description      = "a description"
  ssl_certificates = [google_compute_managed_ssl_certificate.mainnet_ssl[count.index].self_link]
  url_map          = google_compute_url_map.default[count.index].id
}

resource "google_compute_url_map" "default" {
  count           = length(var.node_configs)
  name            = "multichain-partner-mainnet-url-map-${count.index}"
  default_service = google_compute_backend_service.multichain_backend[count.index].id
}

resource "google_compute_url_map" "redirect_default" {
  count = length(var.node_configs)
  name  = "multichain-partner-mainnet-redirect-url-map-${count.index}"
  default_url_redirect {
    strip_query    = false
    https_redirect = true
  }
}

resource "google_compute_backend_service" "multichain_backend" {
  count                 = length(var.node_configs)
  name                  = "multichain-partner-mainnet-backend-service-${count.index}"
  load_balancing_scheme = "EXTERNAL"


  log_config {
    enable      = true
    sample_rate = 0.5
  }
  backend {
    group = google_compute_instance_group.multichain_group[count.index].id
  }

  health_checks = [google_compute_health_check.multichain_healthcheck.id]
}

resource "google_compute_instance_group" "multichain_group" {
  count     = length(var.node_configs)
  name      = "multichain-partner-mainnet-instance-group-${count.index}"
  instances = [module.instances[count.index].self_links[0]]

  zone = var.zone
  named_port {
    name = "http"
    port = 3000
  }
}

resource "google_compute_firewall" "app_port" {
  name    = "allow-multichain-healthcheck-access"
  network = var.network

  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  source_tags   = ["multichain"]

  allow {
    protocol = "tcp"
    ports    = ["80", "3000"]
  }

  depends_on = [module.vpc]
}

resource "google_logging_project_sink" "to_sig_central" {
  name        = "sig-central-logging"
  destination = "logging.googleapis.com/projects/near-cs-mainnet/locations/global/buckets/_Default"

  unique_writer_identity = true
}