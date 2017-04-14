import pytest
from collections import namedtuple
from dirvish_prometheus_metrics import extract_client_scripts


def test_client_scripts():

    TestData = namedtuple('TestData', ['file',
                                       'expected_pre_client_exit_status',
                                       'expected_post_client_exit_status'])

    summary_files = [
        TestData('samples/summary_failed_pre-client', 256, 0),
        TestData('samples/summary_failed_post-client', 0, 1),
        TestData('samples/summary_successful', 0, 0)
    ]

    for test_case in summary_files:

        metrics = extract_client_scripts(test_case.file)

        assert metrics[0].value == test_case.expected_pre_client_exit_status
        assert metrics[1].value == test_case.expected_post_client_exit_status
