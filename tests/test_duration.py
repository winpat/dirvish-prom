import pytest
from collections import namedtuple
from dirvish_prometheus_metrics import extract_duration


def test_duration():

    TestData = namedtuple('TestData', ['file',
                                       'expected_duration_in_seconds',
                                       'expected_completion_timestamp'])

    summary_files = [
        TestData('samples/summary_failed_post-client', 98, 1492023621),
        TestData('samples/summary_successful', 4, 1492024735)
    ]

    for test_case in summary_files:

        metrics = extract_duration(test_case.file)

        assert metrics['dirvish_duration_seconds'].value == test_case.expected_duration_in_seconds
        assert metrics['dirvish_last_completed'].value == test_case.expected_completion_timestamp
