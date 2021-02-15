import pytest
from pytest_lazyfixture import lazy_fixture
from dirvish_prom import (
    get_dirvish_status,
    parse_dirvish_summary,
    parse_rsync_log,
    Metric,
)
from pathlib import Path


@pytest.fixture
def summary_successful():
    return Path("samples/summaries/successful").read_text().split("\n")


@pytest.fixture
def summary_failed_pre_client():
    return Path("samples/summaries/failed_pre_client").read_text().split("\n")


@pytest.fixture
def summary_failed_post_client():
    return Path("samples/summaries/failed_post_client").read_text().split("\n")


@pytest.fixture
def log():
    return Path("samples/log").read_text().split("\n")


@pytest.mark.parametrize(
    "status,expected_value", [("success", 0), ("warning", 1), ("error", 2), ("fail", 3)]
)
def test_get_dirvish_status(monkeypatch, status, expected_value):
    monkeypatch.setenv("DIRVISH_STATUS", status)
    assert get_dirvish_status() == Metric(
        name="dirvish_status",
        description="Dirvish status - success (0), warning (1), error (2) or fail (3)",
        labels={},
        value=expected_value,
    )


@pytest.mark.parametrize(
    "summary,expected_metrics",
    [
        (
            lazy_fixture("summary_successful"),
            [
                Metric(
                    "dirvish_duration_seconds", "Duration of dirvish backup", 4.0, {}
                ),
                Metric(
                    "dirvish_last_completed",
                    "Timestamp of last completed backup",
                    1492024735.0,
                    {},
                ),
            ],
        ),
        (
            lazy_fixture("summary_failed_pre_client"),
            [
                Metric(
                    "dirvish_pre_client_return_code",
                    "Return code of dirvish pre client scripts",
                    256.0,
                    {},
                )
            ],
        ),
        (
            lazy_fixture("summary_failed_post_client"),
            [
                Metric(
                    "dirvish_post_client_return_code",
                    "Return code of dirvish post client scripts",
                    1.0,
                    {},
                ),
                Metric(
                    "dirvish_duration_seconds", "Duration of dirvish backup", 98.0, {}
                ),
                Metric(
                    "dirvish_last_completed",
                    "Timestamp of last completed backup",
                    1492023621.0,
                    {},
                ),
            ],
        ),
    ],
)
def test_parse_dirvish_summary(summary, expected_metrics):
    assert list(parse_dirvish_summary(summary)) == expected_metrics


def test_parse_rsync_log(log):
    assert list(parse_rsync_log(log)) == [
        Metric("rsync_number_files_count", "Number of files", 49158.0, {}),
        Metric("rsync_number_created_files_count", "Number of created files", 46.0, {}),
        Metric("rsync_number_deleted_files_count", "Number of deleted files", 0.0, {}),
        Metric(
            "rsync_number_transferred_files_count",
            "Number of transferred files",
            2181.0,
            {},
        ),
        Metric("rsync_total_file_size_bytes", "Total file size", 1880868297.0, {}),
        Metric(
            "rsync_total_transferred_file_size_bytes",
            "Total of transferred file size",
            488263011.0,
            {},
        ),
        Metric("rsync_literal_data_bytes", "Total of literal data", 122397611.0, {}),
        Metric("rsync_matched_data_bytes", "Total of matched data", 365877132.0, {}),
        Metric("rsync_file_list_size", "Total of file list size", 338039.0, {}),
        Metric(
            "rsync_list_generation_time_seconds",
            "Duration of list generation",
            0.001,
            {},
        ),
        Metric(
            "rsync_list_transfer_time_seconds", "Duration of list transfer", 0.0, {}
        ),
        Metric("rsync_total_bytes_sent", "Total bytes sent", 2900455.0, {}),
        Metric("rsync_total_bytes_received", "Total bytes received", 125497022.0, {}),
    ]
