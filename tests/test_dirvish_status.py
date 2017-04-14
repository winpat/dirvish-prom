import pytest
import os
from dirvish_prometheus_metrics import extract_dirvish_status


def test_dirvish_status():

    statuses = ['success', 'warning', 'error', 'fail']

    for status, expected_status in zip(statuses, range(3)):
        os.environ['DIRVISH_STATUS'] = status
        assert extract_dirvish_status().value == expected_status


