# Dirvish Prometheus Metrics

A [Dirvish](http://dirvish.org) post exec script that extracts various [Prometheus](https://prometheus.io) metrics and writes them to a file.

## Requirements

You want Python version >= 3.6 to run this script.

## Usage

1. Make sure that dirvish runs rsync with the `--stats` flag.
```
stats: t
```
2. Also make sure that the `dirvish_prometheus_metrics` script is added as `post-server` script of each vault:
```
post-server: /usr/local/bin/dirvish_prometheus_metrics.py -o /var/www/vaultname.prom -j dirvish
```

## Exposed Metrics

The `dirvish_prometheus_metrics` script exposes the following metrics:

``` promql
# HELP dirvish_status Dirvish status - success (0), warning (1), error (2) or fail (3).
# TYPE dirvish_status gauge
dirvish_status{server=clu, client=192.168.3.2, vault=vault, branch=default} 0.0
# HELP dirvish_pre_client_return_code Return code of dirvish pre client scripts.
# TYPE dirvish_pre_client_return_code gauge
dirvish_pre_client_return_code{server=clu, client=192.168.3.2, vault=vault, branch=default} 0.0
# HELP dirvish_post_client_return_code Return code of dirvish post client scripts.
# TYPE dirvish_post_client_return_code gauge
dirvish_post_client_return_code{server=clu, client=192.168.3.2, vault=vault, branch=default} 0.0
# HELP rsync_number_files_count Number of files.
# TYPE rsync_number_files_count gauge
rsync_number_files_count{server=clu, client=192.168.3.2, vault=vault, branch=default} 378109.0
# HELP rsync_number_created_files_count Number of created files.
# TYPE rsync_number_created_files_count gauge
rsync_number_created_files_count{server=clu, client=192.168.3.2, vault=vault, branch=default} 0.0
# HELP rsync_number_deleted_files_count Number of deleted files.
# TYPE rsync_number_deleted_files_count gauge
rsync_number_deleted_files_count{server=clu, client=192.168.3.2, vault=vault, branch=default} 0.0
# HELP rsync_number_transferred_files_count Number of transferred files.
# TYPE rsync_number_transferred_files_count gauge
rsync_number_transferred_files_count{server=clu, client=192.168.3.2, vault=vault, branch=default} 530.0
# HELP rsync_total_file_size_bytes Total file size.
# TYPE rsync_total_file_size_bytes gauge
rsync_total_file_size_bytes{server=clu, client=192.168.3.2, vault=vault, branch=default} 339958838087.0
# HELP rsync_total_transferred_file_size_bytes Total of transferred file size.
# TYPE rsync_total_transferred_file_size_bytes gauge
rsync_total_transferred_file_size_bytes{server=clu, client=192.168.3.2, vault=vault, branch=default} 99956824.0
# HELP rsync_literal_data_bytes Total of literal data.
# TYPE rsync_literal_data_bytes gauge
rsync_literal_data_bytes{server=clu, client=192.168.3.2, vault=vault, branch=default} 3062412.0
# HELP rsync_matched_data_bytes Total of matched data.
# TYPE rsync_matched_data_bytes gauge
rsync_matched_data_bytes{server=clu, client=192.168.3.2, vault=vault, branch=default} 96894412.0
# HELP rsync_file_list_size Total of file list size.
# TYPE rsync_file_list_size gauge
rsync_file_list_size{server=clu, client=192.168.3.2, vault=vault, branch=default} 4955071.0
# HELP rsync_list_generation_time_seconds Duration of list generation.
# TYPE rsync_list_generation_time_seconds gauge
rsync_list_generation_time_seconds{server=clu, client=192.168.3.2, vault=vault, branch=default} 0.001
# HELP rsync_list_transfer_time_seconds Duration of list transfer.
# TYPE rsync_list_transfer_time_seconds gauge
rsync_list_transfer_time_seconds{server=clu, client=192.168.3.2, vault=vault, branch=default} 0.0
# HELP rsync_total_bytes_sent Total bytes sent.
# TYPE rsync_total_bytes_sent gauge
rsync_total_bytes_sent{server=clu, client=192.168.3.2, vault=vault, branch=default} 906544.0
# HELP rsync_total_bytes_received Total bytes received.
# TYPE rsync_total_bytes_received gauge
rsync_total_bytes_received{server=clu, client=192.168.3.2, vault=vault, branch=default} 16789542.0
# HELP dirvish_duration_seconds Duration of dirvish backup.
# TYPE dirvish_duration_seconds gauge
dirvish_duration_seconds{server=clu, client=192.168.3.2, vault=vault, branch=default} 9.254926
# HELP dirvish_last_completed Timestamp of last completed backup.
# TYPE dirvish_last_completed gauge
dirvish_last_completed{server=clu, client=192.168.3.2, vault=vault, branch=default} 1549828637.0
```


## Alerting Rules

Here are couple alerting rules that you can use:

``` promql
ALERT DirvishPreClientScriptFailed
  IF dirvish_pre_client_return_code != 0
  FOR 1h
  LABELS {severity="critical"}
  ANNOTATIONS {
	summary="Pre-client script of vault {{ $labels.client }} on server {{ $labels.server }} failed({{ $value }})."
  }

ALERT DirvishPostClientScriptFailed
  IF dirvish_post_client_return_code != 0
  FOR 1h
  LABELS {severity="warning"}
  ANNOTATIONS {
	summary="Post-client script of vault {{ $labels.client }} on server {{ $labels.server }} failed({{ $value }})."
  }

ALERT DirvishBackupUnsuccessful
  IF dirvish_status != 0
  FOR 1h
  LABELS {severity="warning"}
  ANNOTATIONS {
	summary="Dirvish backup of vault {{ $labels.client }} on server {{ $labels.server }} failed({{ $value }})."
  }

ALERT NoDirvishBackupInLast24h
  IF time() - dirvish_last_completed > 3600 * 24
  LABELS {severity="warning"}
  ANNOTATIONS {
	summary="Dirvish backup of vault {{ $labels.client }} on server {{ $labels.server }} has not run in 24 hours."
  }
```

License
-------
GNU GENERAL PUBLIC LICENSE Version 3

See the	[LICENSE](LICENSE) file.
