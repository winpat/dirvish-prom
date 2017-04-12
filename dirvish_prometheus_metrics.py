#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import sys
import requests
import argparse
from datetime import datetime
from collections import namedtuple


class Metric:

    def __init__(self, name, description, value=0):
        self.name = name
        self.description = description
        self.value = value

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
        ''' Template out prometheus metrics '''

        return ('# HELP {} {}.\n'
                '# TYPE {} gauge\n'
                '{} {}\n').format(
                    self.name,
                    self.description,
                    self.name,
                    self.name,
                    self.value)


def parse_arguments():
    ''' Parse command-line arguments '''

    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--pushgateway',
                        help='Pushgateway (e.g. http://pushgateway.example.com)',
                        action='store', default='http://127.0.0.1:9091/')
    parser.add_argument('-j', '--jobname',
                        help='Jobname (e.g "dirvish")',
                        action='store', default='dirvish')

    return parser.parse_args()


def read_file(file):
    ''' Read lines of file into list '''

    try:
        # Read logfile into memory
        with open(file, 'rt') as f:
            lines = f.readlines()

    except FileNotFoundError:
        print('Error: Unable to open file "{}"'.format(file))
        sys.exit(1)

    return lines


def extract_duration(summary_file):
    ''' Extract the duration of a dirvish backup and the timestamp of the last 
    completed backup '''

    lines = read_file(summary_file)
    begin, complete = datetime.now(), datetime.now()

    for line in lines:
        if line.startswith("Backup-begin:"):
            match = re.match('^Backup-begin: ([\d\-:\s]{19})$', line)
            begin = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')

        elif line.startswith("Backup-complete:"):
            match = re.match('^Backup-complete: ([\d\-:\s]{19})$', line)
            complete = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')

    return [Metric('dirvish_duration_seconds',
                  'Duration of dirvish backup',
                   (complete - begin).total_seconds()),
            Metric('dirvish_last_completed',
                  'Timestamp of last completed backup',
                   complete.strftime('%s'))]


def extract_rsync_metrics(logfile):
    ''' Turn the output of `rsync --stats ...` into Prometheus metrics. '''

    patterns = ['^Number of files: ([\d\,]*)\s?.*?$',
                '^Number of created files: ([\d\,]*)\s?.*?$',
                '^Number of deleted files: ([\d\,]*)\s?.*?$',
                '^Number of regular files transferred: ([\d\,]*)\s?.*?$',
                '^Total file size: ([\d\,]*?) bytes$',
                '^Total transferred file size: ([\d\,]*?) bytes$',
                '^Literal data: ([\d\,]*?) bytes$',
                '^Matched data: ([\d\,]*?) bytes$',
                '^File list size: ([\d\,]*?)$',
                '^File list generation time: ([\d\.]*?) seconds$',
                '^File list transfer time: ([\d\.]*?) seconds$',
                '^Total bytes sent: ([\d\,]*?)$',
                '^Total bytes received: ([\d\,]*?)$']

    metrics = [Metric('rsync_number_files_count',
                      'Number of files'),
               Metric('rsync_number_created_files_count',
                      'Number of created files'),
               Metric('rsync_number_deleted_files_count',
                      'Number of deleted files'),
               Metric('rsync_number_transferred_files_count',
                      'Number of transferred files'),
               Metric('rsync_total_file_size_bytes',
                      'Total file size'),
               Metric('rsync_total_transferred_file_size_bytes',
                      'Total of transferred file size'),
               Metric('rsync_literal_data_bytes',
                      'Total of literal data'),
               Metric('rsync_matched_data_bytes',
                      'Total of matched data'),
               Metric('rsync_file_list_size',
                      'Total of file list size'),
               Metric('rsync_list_generation_time_seconds',
                      'Duration of list generation'),
               Metric('rsync_list_transfer_time_seconds',
                      'Duration of list transfer'),
               Metric('rsync_total_bytes_sent',
                      'Total bytes sent'),
               Metric('rsync_total_bytes_received',
                      'Total bytes received')]

    lines = read_file(logfile)

    # Dirvish log files can have variable lengths depending on the how many
    # files have been transferred. To make the metric parsing easier cut away
    # everything until the stats.
    for index, line in enumerate(lines):
        if line.startswith('Number of files:'):
            offset = index

    if not offset:
        print('Error: Unable to parse logfile')
        sys.exit(1)

    # Cut away log of transferred files
    rsync_stats = lines[offset:]

    for i, (metric, pattern) in enumerate(zip(metrics, patterns)):
        # Extract metrics from rsync stats
        match = re.match(pattern, rsync_stats[i])
        metric.value = match.group(1)


    return metrics


def extract_dirvish_status():
    ''' Returns the environemnt variable DIRVISH_STATUS mapped to an integer.

    0 - success
    1 - warning
    2 - error
    3 - fail
    '''

    status = os.getenv('DIRVISH_STATUS')
    options = {'success':     0,
               'warning':     1,
               'error':       2,
               'fail':        3}

    return Metric('dirvish_status',
                  'Dirvish status - success (0), warning (1), error (2) or fail (3)',
                  options[status])


def extract_client_scripts(summary_file):
    '''Returns the return code of the dirvish pre-client and post-client script
    or 0 if no script is defined.

    Dirvish allows to run pre-server, pre-client, post-client and post-server
    scripts.

    Failure of the pre-server or post-server command will halt all further
    action. So this script won't run either.

    Failure of the pre-client command will prevent the rsync from running and
    the post-server command, if any, will be run.
    '''

    lines = read_file(summary_file)

    pre_client = Metric('dirvish_pre_client_return_code',
                        'Return code of dirvish pre client scripts')
    post_client = Metric('dirvish_post_client_return_code',
                         'Return code of dirvish post client scripts')

    for line in lines:
        if line.startswith('pre-client failed'):
            match = re.match('^pre-client failed \((\d*)\)$', line)
            pre_client.value = match.group(1) if match != None else 0

            if pre_client.value != 0:
                raise RuntimeError(pre_client)

        if line.startswith('post-client failed'):
            match = re.match('^post-client failed \((\d*)\)$', line)
            post_client.value = match.group(1) if match != None else 0

    return [pre_client, post_client]


def compose_pushgateway_url(host, jobname, labels):
    ''' Returns the url to the pushgateway that group the job by labels '''

    # Turn label dict into url string ("/LABEL_NAME/LABEL_VALUE"
    label_string = '/'.join(['%s/%s' % (key, value) for (key, value) in labels.items()])

    return '{}/metrics/job/{}/{}'.format(host.strip('/'), jobname, label_string)


def push_to_pushgateway(url, metrics):
    ''' Push metrics to the pushgateway '''

    data = ''.join([str(metric) for metric in metrics]).encode('utf-8')
    response = requests.put(url, data=data)
    print('Pushed metrics to the pushgateway "{}" (Status code: "{}", Content:"{}")'
          .format(url, response.status_code, response.text))



if __name__ == '__main__':

    # Default labels that will be attached to each metric
    labels = {'server': os.getenv('DIRVISH_SERVER'),
              'client': os.getenv('DIRVISH_CLIENT')}

    # Path to dirvish vault instance
    instance = '/' + os.getenv('DIRVISH_DEST').strip('/tree')

    # Global variable that will store prometheus metrics
    metrics = []

    args = parse_arguments()

    logfile = instance + '/log'
    summary_file = instance + '/summary'

    # Try to gather as many metrics as possible. However if for example the pre-client fails, there
    # will be no rsync stats to parse... In this case skip the rest.
    try:
        metrics.append(extract_dirvish_status())
        metrics.extend(extract_client_scripts(summary_file))
        metrics.extend(extract_rsync_metrics(logfile))
        metrics.extend(extract_duration(summary_file))

    except RuntimeError as metric:
        # Add the metric that caused the exception
        metrics.append(metric)

    for metric in metrics:
        print(str(metric))

    url = compose_pushgateway_url(args.pushgateway, args.jobname, labels)
    push_to_pushgateway(url, metrics)
