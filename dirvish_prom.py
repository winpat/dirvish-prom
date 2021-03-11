#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
from sys import exit
from collections import deque
from datetime import datetime
from itertools import chain
from pathlib import Path


class Metric:
    def __init__(self, name, description, value=0, labels={}):
        self.name = name
        self.description = description
        self.value = value
        self.labels = labels

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, v):

        # Remove commas in string before converting to double. Rsync metrics
        # sometimes use commas to group digits.
        # (e.g. "File list size: 338,039")
        if type(v) is str:
            v = v.replace(",", "")

        # Prometheus uses 64-bit floats to store samples
        self.__value = float(v)

    def __eq__(self, o):
        return (
            self.name == o.name
            and self.description == o.description
            and self.value == o.value
            and self.labels == o.labels
        )

    def __repr__(self):
        return f"Metric({self.name}, {self.description}, {self.value}, {self.labels})"

    def __str__(self):
        """ Template out prometheus metrics """

        labels = ",".join(f'{k}="{v}"' for k, v in self.labels.items())

        return (
            f"# HELP {self.name} {self.description}.\n"
            f"# TYPE {self.name} gauge\n"
            f"{self.name}{{{labels}}} {self.value}\n"
        )


RSYNC_METRICS = [
    (
        r"^Number of files: ([\d\,]*)\s?.*?$",
        "rsync_number_files_count",
        "Number of files",
    ),
    (
        r"^Number of created files: ([\d\,]*)\s?.*?$",
        "rsync_number_created_files_count",
        "Number of created files",
    ),
    (
        r"^Number of deleted files: ([\d\,]*)\s?.*?$",
        "rsync_number_deleted_files_count",
        "Number of deleted files",
    ),
    (
        r"^Number of regular files transferred: ([\d\,]*)\s?.*?$",
        "rsync_number_transferred_files_count",
        "Number of transferred files",
    ),
    (
        r"^Total file size: ([\d\,]*?) bytes$",
        "rsync_total_file_size_bytes",
        "Total file size",
    ),
    (
        r"^Total transferred file size: ([\d\,]*?) bytes$",
        "rsync_total_transferred_file_size_bytes",
        "Total of transferred file size",
    ),
    (
        r"^Literal data: ([\d\,]*?) bytes$",
        "rsync_literal_data_bytes",
        "Total of literal data",
    ),
    (
        r"^Matched data: ([\d\,]*?) bytes$",
        "rsync_matched_data_bytes",
        "Total of matched data",
    ),
    (
        r"^File list size: ([\d\,]*?)$",
        "rsync_file_list_size",
        "Total of file list size",
    ),
    (
        r"^File list generation time: ([\d\.]*?) seconds$",
        "rsync_list_generation_time_seconds",
        "Duration of list generation",
    ),
    (
        r"^File list transfer time: ([\d\.]*?) seconds$",
        "rsync_list_transfer_time_seconds",
        "Duration of list transfer",
    ),
    (r"^Total bytes sent: ([\d\,]*?)$", "rsync_total_bytes_sent", "Total bytes sent"),
    (
        r"^Total bytes received: ([\d\,]*?)$",
        "rsync_total_bytes_received",
        "Total bytes received",
    ),
]


def parse_rsync_log(lines):

    lines = deque(lines)
    while lines and not lines[0].startswith("Number of files:"):
        lines.popleft()

    for line, metric in zip(lines, RSYNC_METRICS):
        pattern, name, desc = metric
        match = re.match(pattern, line)
        yield Metric(name, desc, match.group(1))


def parse_dirvish_summary(lines):

    begin = None
    complete = None

    for line in lines:

        if line.startswith("pre-client failed"):
            match = re.match(r"^pre-client failed \((\d*)\)$", line)
            yield Metric(
                "dirvish_pre_client_return_code",
                "Return code of dirvish pre client scripts",
                match.group(1),
            )
            continue

        if line.startswith("post-client failed"):
            match = re.match(r"^post-client failed \((\d*)\)$", line)
            yield Metric(
                "dirvish_post_client_return_code",
                "Return code of dirvish post client scripts",
                match.group(1),
            )
            continue

        if line.startswith("Backup-begin:"):
            match = re.match("^Backup-begin: ([\d\-:\s]{19})$", line)
            begin = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
            continue

        if line.startswith("Backup-complete:"):
            match = re.match("^Backup-complete: ([\d\-:\s]{19})$", line)
            complete = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
            continue

    if begin and complete:
        yield Metric(
            "dirvish_duration_seconds",
            "Duration of dirvish backup",
            (complete - begin).total_seconds(),
        )

    if complete:
        yield Metric(
            "dirvish_last_completed",
            "Timestamp of last completed backup",
            complete.strftime("%s"),
        )


def get_dirvish_status():
    options = {"success": 0, "warning": 1, "error": 2, "fail": 3}
    status = options.get(os.getenv("DIRVISH_STATUS"), 3)
    yield Metric(
        "dirvish_status",
        "Dirvish status - success (0), warning (1), error (2) or fail (3)",
        status,
    )


def parse_arguments():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--out-directory",
        help="Path to the textfile collector directory",
        action="store",
        default="/var/lib/prometheus-node-exporter-text-files",
    )
    return parser.parse_args()


def main():

    if not os.getenv("DIRVISH_STATUS"):
        print("Not running as a post client script, terminating.")
        exit(1)

    vault, branch, _ = os.getenv("DIRVISH_IMAGE").split(":")
    labels = {
        "server": os.getenv("DIRVISH_SERVER"),
        "client": os.getenv("DIRVISH_CLIENT"),
        "vault": vault,
        "branch": branch,
    }

    # Strip /tree from the image destination path.
    image_path = Path(os.getenv("DIRVISH_DEST")[:-5])

    summary_file = image_path / "summary"
    summary_lines = summary_file.read_text().split("\n")

    log_file = image_path / "log"
    log_lines = log_file.read_text().split("\n")

    metrics = [
        metric
        for metric in chain(
            get_dirvish_status(),
            parse_dirvish_summary(summary_lines),
            parse_rsync_log(log_lines),
        )
    ]

    args = parse_arguments()
    out_dir = Path(args.out_directory)
    with open(out_dir / f"dirvish_{vault}_{branch}.prom", "w") as f:
        for metric in metrics:
            metric.labels = labels
            print(metric)
            f.write(str(metric))


if __name__ == "__main__":
    main()
