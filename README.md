Dirvish Prometheus Metrics
==========================
[![Travis](https://img.shields.io/travis/winpat/dirvish_prometheus_metrics.svg?style=flat-square)](https://travis-ci.org/adfinis-sygroup/vault-client)
[![License](https://img.shields.io/github/license/winpat/dirvish_prometheus_metrics.svg?style=flat-square)](LICENSE)

A [Dirvish](http://dirvish.org) post exec script that extracts various [Prometheus](https://prometheus.io) metrics and pushes them to a [Pushgateway](https://github.com/prometheus/pushgateway).

Install
-------
1. The `dirvish_prometheus_metrics` script requires python3 and the requests library. In Debian you can
install those through:
```
apt-get install python3 python3-requests
```
2. Download the [latest release](https://github.com/winpat/dirvish_prometheus_metrics/releases).

Usage
-----
1. Make sure that dirvish runs rsync with the `--stats` flag. You can enforce this globally in the
   `/etc/dirvish/master.conf`:

```
stats: t
```
2. Also make sure that the `dirvish_prometheus_metrics` script is added as `post-server` script:
```
post-server: /usr/local/bin/dirvish_prometheus_metrics.py -p 'http://pushgateway.example.com' -j 'dirvish'
```

Exposed Metrics
---------------
The `dirvish_prometheus_metrics` script exposes the following metrics:

``` promql
# HELP dirvish_status Dirvish status - success (0), warning (1), error (2) or fail (3).
# TYPE dirvish_status gauge
dirvish_status 0

# HELP dirvish_pre_client_return_code Return code of dirvish pre client scripts.
# TYPE dirvish_pre_client_return_code gauge
dirvish_pre_client_return_code 0

# HELP dirvish_post_client_return_code Return code of dirvish post client scripts.
# TYPE dirvish_post_client_return_code gauge
dirvish_post_client_return_code 1

# HELP rsync_number_files_count Number of files.
# TYPE rsync_number_files_count gauge
rsync_number_files_count 59127

# HELP rsync_number_created_files_count Number of created files.
# TYPE rsync_number_created_files_count gauge
rsync_number_created_files_count 2

# HELP rsync_number_deleted_files_count Number of deleted files.
# TYPE rsync_number_deleted_files_count gauge
rsync_number_deleted_files_count 0

# HELP rsync_number_transferred_files_count Number of transferred files.
# TYPE rsync_number_transferred_files_count gauge
rsync_number_transferred_files_count 124

# HELP rsync_total_file_size_bytes Total file size.
# TYPE rsync_total_file_size_bytes gauge
rsync_total_file_size_bytes 1.48965e+09

# HELP rsync_total_transferred_file_size_bytes Total of transferred file size.
# TYPE rsync_total_transferred_file_size_bytes gauge
rsync_total_transferred_file_size_bytes 2.69005e+07

# HELP rsync_literal_data_bytes Total of literal data.
# TYPE rsync_literal_data_bytes gauge
rsync_literal_data_bytes 5.14969e+06

# HELP rsync_matched_data_bytes Total of matched data.
# TYPE rsync_matched_data_bytes gauge
rsync_matched_data_bytes 2.17508e+07

# HELP rsync_file_list_size Total of file list size.
# TYPE rsync_file_list_size gauge
rsync_file_list_size 354848

# HELP rsync_list_generation_time_seconds Duration of list generation.
# TYPE rsync_list_generation_time_seconds gauge
rsync_list_generation_time_seconds 0.001

# HELP rsync_list_transfer_time_seconds Duration of list transfer.
# TYPE rsync_list_transfer_time_seconds gauge
rsync_list_transfer_time_seconds 0

# HELP rsync_total_bytes_sent Total bytes sent.
# TYPE rsync_total_bytes_sent gauge
rsync_total_bytes_sent 50370

# HELP rsync_total_bytes_received Total bytes received.
# TYPE rsync_total_bytes_received gauge
rsync_total_bytes_received 6.70428e+06

# HELP dirvish_duration_seconds Duration of dirvish backup.
# TYPE dirvish_duration_seconds gauge
dirvish_duration_seconds 5.54635
```



Alerting Rules
--------------
Here are couple alerting rules that you can use:
``` promql
ALERT DirvishPreClientScriptFailed
  IF dirvish_post_client_return_code != 0
  LABELS {severity="critical"}
  ANNOTATIONS {
	summary="Pre-client script of vault {{ $labels.client }} on server {{ $labels.server }} failed."
  }
```

License
-------
GNU GENERAL PUBLIC LICENSE Version 3

See the	[LICENSE](LICENSE) file.
