import pytest
import os
from dirvish_prometheus_metrics import extract_dirvish_status


def test_dirvish_status():

    statuses = {
             'success': 0, 
             'warning': 1, 
             'error':   2, 
             'fail':    3,
    }



    for status_name, expected_status_value in statuses.items():

        metrics = extract_dirvish_status(status_name)

        assert metrics['dirvish_status'].value == expected_status_value


