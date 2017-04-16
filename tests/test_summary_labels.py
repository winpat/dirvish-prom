import pytest
from collections import namedtuple
from dirvish_prometheus_metrics import extract_summary_labels


def test_summary_labels():

    TestCase = namedtuple('TestData', ['file',
                                       'expected_branch_label',
                                       'expected_vault_label'])

    cases = [
        TestCase('samples/summary_failed_post-client', 'default',
                 'pathfinder.intra.winpat.ch'),
    ]

    for case in cases:

        labels = extract_summary_labels(case.file)

        assert labels['branch'] == case.expected_branch_label
        assert labels['vault'] == case.expected_vault_label
