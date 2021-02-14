import pytest
from collections import namedtuple
from dirvish_prom import extract_client_scripts
from dirvish_prom import extract_dirvish_status
from dirvish_prom import extract_duration
from dirvish_prom import Metric, extract_rsync_metrics
from dirvish_prom import extract_summary_labels


def test_client_scripts():

    TestData = namedtuple(
        "TestData",
        ["file", "expected_pre_client_exit_status", "expected_post_client_exit_status"],
    )

    summary_files = [
        TestData("samples/summary_failed_pre-client", 256, 0),
        TestData("samples/summary_failed_post-client", 0, 1),
        TestData("samples/summary_successful", 0, 0),
    ]

    for test_case in summary_files:

        metrics = extract_client_scripts(test_case.file)

        assert (
            metrics["dirvish_pre_client_return_code"].value
            == test_case.expected_pre_client_exit_status
        )
        assert (
            metrics["dirvish_post_client_return_code"].value
            == test_case.expected_post_client_exit_status
        )


def test_dirvish_status():

    statuses = {
        "success": 0,
        "warning": 1,
        "error": 2,
        "fail": 3,
    }

    for status_name, expected_status_value in statuses.items():

        metrics = extract_dirvish_status(status_name)

        assert metrics["dirvish_status"].value == expected_status_value


def test_duration():

    TestData = namedtuple(
        "TestData",
        ["file", "expected_duration_in_seconds", "expected_completion_timestamp"],
    )

    summary_files = [
        TestData("samples/summary_failed_post-client", 98, 1492023621),
        TestData("samples/summary_successful", 4, 1492024735),
    ]

    for test_case in summary_files:

        metrics = extract_duration(test_case.file)

        assert (
            metrics["dirvish_duration_seconds"].value
            == test_case.expected_duration_in_seconds
        )
        assert (
            metrics["dirvish_last_completed"].value
            == test_case.expected_completion_timestamp
        )


def test_rsync_metrics():

    test_logfile = "samples/log"

    expected_metrics = [
        Metric("rsync_number_files_count", "Number of files", 49158),
        Metric("rsync_number_created_files_count", "Number of created files", 46),
        Metric("rsync_number_deleted_files_count", "Number of deleted files", 0),
        Metric(
            "rsync_number_transferred_files_count", "Number of transferred files", 2181
        ),
        Metric("rsync_total_file_size_bytes", "Total file size", 1880868297),
        Metric(
            "rsync_total_transferred_file_size_bytes",
            "Total of transferred file size",
            488263011,
        ),
        Metric("rsync_literal_data_bytes", "Total of literal data", 122397611),
        Metric("rsync_matched_data_bytes", "Total of matched data", 365877132),
        Metric("rsync_file_list_size", "Total of file list size", 338039),
        Metric(
            "rsync_list_generation_time_seconds", "Duration of list generation", 0.001
        ),
        Metric("rsync_list_transfer_time_seconds", "Duration of list transfer", 0.000),
        Metric("rsync_total_bytes_sent", "Total bytes sent", 2900455),
        Metric("rsync_total_bytes_received", "Total bytes received", 125497022),
    ]

    metrics = extract_rsync_metrics(test_logfile)

    for metric, expected_metric in zip(metrics.values(), expected_metrics):
        assert metric.value == expected_metric.value


def test_summary_labels():

    TestCase = namedtuple(
        "TestData", ["file", "expected_branch_label", "expected_vault_label"]
    )

    cases = [
        TestCase(
            "samples/summary_failed_post-client",
            "default",
            "pathfinder.intra.winpat.ch",
        ),
    ]

    for case in cases:

        labels = extract_summary_labels(case.file)

        assert labels["branch"] == case.expected_branch_label
        assert labels["vault"] == case.expected_vault_label
