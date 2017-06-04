import pytest
from dirvish_prometheus_metrics import Metric, extract_rsync_metrics


def test_rsync_metrics():

    test_logfile = 'samples/log'

    expected_metrics = [
        Metric('rsync_number_files_count',
               'Number of files',
               49158),
        Metric('rsync_number_created_files_count',
               'Number of created files',
               46),
        Metric('rsync_number_deleted_files_count',
               'Number of deleted files',
               0),
        Metric('rsync_number_transferred_files_count',
               'Number of transferred files',
               2181),
        Metric('rsync_total_file_size_bytes',
               'Total file size',
               1880868297),
        Metric('rsync_total_transferred_file_size_bytes',
               'Total of transferred file size',
               488263011),
        Metric('rsync_literal_data_bytes',
               'Total of literal data',
               122397611),
        Metric('rsync_matched_data_bytes',
               'Total of matched data',
               365877132),
        Metric('rsync_file_list_size',
               'Total of file list size',
               338039),
        Metric('rsync_list_generation_time_seconds',
               'Duration of list generation',
               0.001),
        Metric('rsync_list_transfer_time_seconds',
               'Duration of list transfer',
               0.000),
        Metric('rsync_total_bytes_sent',
               'Total bytes sent',
               2900455),
        Metric('rsync_total_bytes_received',
               'Total bytes received',
               125497022)
    ]
   
    metrics = extract_rsync_metrics(test_logfile)

    for metric, expected_metric in zip(metrics.values(), expected_metrics):
        assert metric.value == expected_metric.value

