output "node_public_ip" {
  value = google_compute_global_address.external_ips[*].address
}

output "central_sink_writer_identity" {
  value = google_logging_project_sink.to_sig_central.writer_identity
}