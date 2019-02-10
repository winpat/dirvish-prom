#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
from datetime import datetime
from pprint import pprint


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
        if isinstance(v, str):
            v = v.replace(",", "")

        # Prometheus uses 64-bit floats to store samples
        self.__value = float(v)

    def __str__(self):
        """ Template out prometheus metrics """

        lables = ','.join(f'{k}="{v}"' for k, v in self.labels.items())

        return (
            f"# HELP {self.name} {self.description}.\n"
            f"# TYPE {self.name} gauge\n"
            f"{self.name}{labels} {self.value}\n"
        )


def parse_arguments():
    """ Parse command-line arguments """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-o",
        "--outfile",
        help="Path to output file",
        action="store",
    )
    parser.add_argument(
        "-j",
        "--jobname",
        help='Jobname (e.g "dirvish")',
        action="store",
        default="dirvish",
    )

    return parser.parse_args()


def read_file(file):
    """ Read lines of file into list """

    try:
        # Read logfile into memory
        with open(file, "rt") as f:
            lines = f.readlines()

    except FileNotFoundError:
        print('Error: Unable to open file "{}"'.format(file))
        sys.exit(1)

    return lines


def extract_summary_labels(summary_file):
    """ Extract `vault` and `branch` label from summary file """

    lines = read_file(summary_file)
    labels = {}

    for line in lines:
        if line.startswith("branch:"):
            match = re.match("^branch: (.*)$", line)
            labels["branch"] = match.group(1)

        if line.startswith("vault:"):
            match = re.match("^vault: (.*$)", line)
            labels["vault"] = match.group(1)

    return labels


def extract_duration(summary_file):
    """ Extract the duration of a dirvish backup and the timestamp of the last
    completed backup """

    lines = read_file(summary_file)
    begin, complete = datetime.now(), datetime.now()

    for line in lines:
        if line.startswith("Backup-begin:"):
            match = re.match("^Backup-begin: ([\d\-:\s]{19})$", line)
            begin = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")

        elif line.startswith("Backup-complete:"):
            match = re.match("^Backup-complete: ([\d\-:\s]{19})$", line)
            complete = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")

    return {
        "dirvish_duration_seconds": Metric(
            "dirvish_duration_seconds",
            "Duration of dirvish backup",
            (complete - begin).total_seconds(),
        ),
        "dirvish_last_completed": Metric(
            "dirvish_last_completed",
            "Timestamp of last completed backup",
            complete.strftime("%s"),
        ),
    }


def extract_rsync_metrics(logfile):
    """ Turn the output of `rsync --stats ...` into Prometheus metrics. """

    patterns = [
        "^Number of files: ([\d\,]*)\s?.*?$",
        "^Number of created files: ([\d\,]*)\s?.*?$",
        "^Number of deleted files: ([\d\,]*)\s?.*?$",
        "^Number of regular files transferred: ([\d\,]*)\s?.*?$",
        "^Total file size: ([\d\,]*?) bytes$",
        "^Total transferred file size: ([\d\,]*?) bytes$",
        "^Literal data: ([\d\,]*?) bytes$",
        "^Matched data: ([\d\,]*?) bytes$",
        "^File list size: ([\d\,]*?)$",
        "^File list generation time: ([\d\.]*?) seconds$",
        "^File list transfer time: ([\d\.]*?) seconds$",
        "^Total bytes sent: ([\d\,]*?)$",
        "^Total bytes received: ([\d\,]*?)$",
    ]

    metrics = {
        "rsync_number_files_count": Metric(
            "rsync_number_files_count", "Number of files"
        ),
        "rsync_number_created_files_count": Metric(
            "rsync_number_created_files_count", "Number of created files"
        ),
        "rsync_number_deleted_files_count": Metric(
            "rsync_number_deleted_files_count", "Number of deleted files"
        ),
        "rsync_number_transferred_files_count": Metric(
            "rsync_number_transferred_files_count", "Number of transferred files"
        ),
        "rsync_total_file_size_bytes": Metric(
            "rsync_total_file_size_bytes", "Total file size"
        ),
        "rsync_total_transferred_file_size_bytes": Metric(
            "rsync_total_transferred_file_size_bytes", "Total of transferred file size"
        ),
        "rsync_literal_data_bytes": Metric(
            "rsync_literal_data_bytes", "Total of literal data"
        ),
        "rsync_matched_data_bytes": Metric(
            "rsync_matched_data_bytes", "Total of matched data"
        ),
        "rsync_file_list_size": Metric(
            "rsync_file_list_size", "Total of file list size"
        ),
        "rsync_list_generation_time_seconds": Metric(
            "rsync_list_generation_time_seconds", "Duration of list generation"
        ),
        "rsync_list_transfer_time_seconds": Metric(
            "rsync_list_transfer_time_seconds", "Duration of list transfer"
        ),
        "rsync_total_bytes_sent": Metric("rsync_total_bytes_sent", "Total bytes sent"),
        "rsync_total_bytes_received": Metric(
            "rsync_total_bytes_received", "Total bytes received"
        ),
    }

    lines = read_file(logfile)

    # Dirvish log files can have variable lengths depending on the how many
    # files have been transferred. To make the metric parsing easier cut away
    # everything until the stats.
    for index, line in enumerate(lines):
        if line.startswith("Number of files:"):
            offset = index

    if not offset:
        print("Error: Unable to parse logfile")
        sys.exit(1)

    # Cut away log of transferred files
    rsync_stats = lines[offset:]

    for i, (metric, pattern) in enumerate(zip(metrics.values(), patterns)):
        # Extract metrics from rsync stats
        match = re.match(pattern, rsync_stats[i])
        metric.value = match.group(1)

    return metrics


def extract_dirvish_status(status):
    """ Returns the environemnt variable DIRVISH_STATUS mapped to an integer.

    0 - success
    1 - warning
    2 - error
    3 - fail
    """

    options = {"success": 0, "warning": 1, "error": 2, "fail": 3}

    # Assume the backup failed if no environment variable is set
    if status:
        status = options.get(status)
    else:
        status = 3

    return {
        "dirvish_status": Metric(
            "dirvish_status",
            "Dirvish status - success (0), warning (1), error (2) or fail (3)",
            status,
        )
    }


def extract_client_scripts(summary_file):
    """Returns the return code of the dirvish pre-client and post-client script
    or 0 if no script is defined.

    Dirvish allows to run pre-server, pre-client, post-client and post-server
    scripts.

    Failure of the pre-server or post-server command will halt all further
    action. So this script won't run either.

    Failure of the pre-client command will prevent the rsync from running and
    the post-server command, if any, will be run.
    """

    lines = read_file(summary_file)

    metrics = {
        "dirvish_pre_client_return_code": Metric(
            "dirvish_pre_client_return_code",
            "Return code of dirvish pre client scripts",
        ),
        "dirvish_post_client_return_code": Metric(
            "dirvish_post_client_return_code",
            "Return code of dirvish post client scripts",
        ),
    }

    for line in lines:
        if line.startswith("pre-client failed"):
            match = re.match("^pre-client failed \((\d*)\)$", line)
            metrics["dirvish_pre_client_return_code"].value = (
                match.group(1) if match != None else 0
            )

        if line.startswith("post-client failed"):
            match = re.match("^post-client failed \((\d*)\)$", line)
            metrics["dirvish_post_client_return_code"].value = (
                match.group(1) if match != None else 0
            )

    return metrics


def write_to_file(path, metrics):
    "Write metrics to file"

    data = "".join(str(m) for m in metrics.values())

    with open(path, 'w') as f:
        f.write(data)



if __name__ == "__main__":

    envvars = {
        "DIRVISH_DEST": os.getenv("DIRVISH_DEST"),
        "DIRVISH_SERVER": os.getenv("DIRVISH_SERVER"),
        "DIRVISH_CLIENT": os.getenv("DIRVISH_CLIENT"),
        "DIRVISH_STATUS": os.getenv("DIRVISH_STATUS"),
    }

    print("Printing Dirvish environment variables:")
    pprint(envvars)

    # Path to dirvish vault instance
    instance = "/" + envvars["DIRVISH_DEST"].strip("/tree")

    # Global variable that will store prometheus metrics
    metrics = {}

    args = parse_arguments()

    logfile = instance + "/log"
    summary_file = instance + "/summary"

    # Default labels that will be attached to each metric
    labels = {"server": envvars["DIRVISH_SERVER"], "client": envvars["DIRVISH_CLIENT"]}

    # Extract additional labels from the summary file
    labels.update(extract_summary_labels(summary_file))

    metrics.update(extract_dirvish_status(envvars["DIRVISH_STATUS"]))
    metrics.update(extract_client_scripts(summary_file))

    # Set labels all metrics
    for k in metrics:
        metrics[k].labels = labels

    # Check if dirvish pre-client script failed and if so abort the collection
    # of further metrics
    if (
        metrics["dirvish_status"].value == 0
        or metrics["dirvish_pre_client_return_code"].value != 0
    ):
        metrics.update(extract_rsync_metrics(logfile))
        metrics.update(extract_duration(summary_file))

    # Print metrics to the summary file
    pprint(metrics.values())

    write_to_file(args.outfile, metrics)
