#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import sys
import argparse
from datetime import datetime
from collections import namedtuple


class Metric:

    def __init__(name, description, value, labels={}):
        self.name = name
        self.description = description
        self.value = value
        self.labels = labels

    def __str__():
        ''' Template out prometheus metrics '''
    
        value = double(value.replace(",", ""))
    
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
    parser.add_argument("-l", "--logfile", help="Name of the logfile (e.g log.gz)",
                        action="store_true", default="log.gz")
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
    ''' Extract the duration of a dirvish backup '''

    lines = read_file(summary_file)

    for line in lines:
        if line.startswith("Backup-begin:"):
            match = re.match('^Backup-begin: ([\d\-: ]{19}).*$', line)
            start = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')

        if line.startswith("Backup-complete:"):
            match = re.match('^Backup-begin: ([\d\-: ]{19}).*$', line)
            end = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')

    return Metric('dirvish_duration_seconds',
                  'Duration of dirvish backup',
                  (end - start).total_seconds())


def extract_rsync_metrics(logfile):
    ''' Turn the output of `rsync --stats ...` into Prometheus metrics. '''

    patterns = ['^Number of files: ([0-9\,]*?) .*$',
                '^Number of created files: ([0-9\,]*?) .*$',
                '^Number of deleted files: ([0-9\,]*?)$',
                '^Number of regular files transferred: ([0-9\,]*?)?$',
                '^Total file size: ([0-9\,]*?) bytes$',
                '^Total transferred file size: ([0-9\,]*?) bytes$',
                '^Literal data: ([0-9\,]*?) bytes$',
                '^Matched data: ([0-9\,]*?) bytes$',
                '^File list size: ([0-9\,]*?)$',
                '^File list generation time: ([0-9\.]*?) seconds$',
                '^File list transfer time: ([0-9\.]*?) seconds$',
                '^Total bytes sent: ([0-9\,]*?)$',                
                '^Total bytes received: ([0-9\,]*?)$']

    metrics = [Metric('rsync_number_files_count',
                      'Number of files',
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

    # Dirvish log files can have variable lengths depending on the how many files have been
    # transferred. To make the metric parsing easier cut away everything until the stats.
    offset = [x for index, line in enumerate(lines) if line.startswith("Number of files:")]

    if not offset:
        print('Error: Unable to parse logfile')
        sys.exit(1)
        
    # Cut away log of transferred files
    rsync_stats = lines[offset:]
                 
    for pattern, metric in zip(metrics, patterns):
        # Extract metrics from rsync stats
        match = re.match(pattern, rsync_stats[metric.line])
        metric.value = match.group(1)

    return metrics


def extract_dirvish_status():
    ''' Returns the environemnt variable DIRVISH_STATUS mapped to an integer.

    0 - success 
    1 - warning
    2 - error
    3 - fatal error
    '''

    status = os.getenv('DIRVISH_STATUS')   
    options = {'success':     0,
               'warning':     1,
               'error':       2,
               'fatal error': 3}

    return Metric('dirvish_status',
                  'Dirvish status success (0), warning (1), error (2), or fatal error (3)',
                  options[status])


def check_pre_post_client_scripts():
    ''' Returns the return code of dirvish pre client and post-client script

    Dirvish allows to run pre-server, pre-client, post-client and post-server scripts.

    Failure of the pre-server command will halt all further action. So this post-server script won't
    run either.

    Failure of the pre-client command will prevent the rsync from running and the post-server
    command, if any, will be run.
    '''

    lines = read_file(summary_file)
    metrics = []

    for line in lines:
        if line.startswith('pre-client failed'):
            match = re.match('^pre-client failed \((\d*)\)$', line)
            metrics.append(Metric('dirvish_pre_client_return_code',
                                  'Return code of dirvish pre client scripts'
                                  match.group(1))

        if line.startswith('post-client failed'):
            match = re.match('^post-client failed \((\d*)\)$', line)
            metrics.append(Metric('dirvish_post_client_return_code',
                                  'Return code of dirvish post client scripts'
                                  match.group(1))

    return metrics



# Post shell_commands will also have DIRVISH_STATUS set to success, warning, error, or fatal error.

if __name__ == '__main__':

    print(os.getenv('DIRVISH_STATUS'))

    # Default labels that will be attached to each metric
    labels = {'job':    'dirvish',
              'server': os.getenv('DIRVISH_SERVER'),
              'client': os.getenv('DIRVISH_CLIENT'),
              'image':  os.getenv('DIRVISH_IMAGE')}

    # Path to dirvish vault instance
    instance = '/' + os.getenv('DIRVISH_DEST').strip('/tree')

    # Global variable that will store prometheus metrics
    metrics = []
    
    args = parse_arguments()

    logfile = instance + args.logfile
    summaryfile = instance + 'summary'
    errorfile = instance + 'error'
            
    metrics += (extract_rsync_metrics(logfile),
                [extract_duration(summaryfile)],
                [extract_dirvish_status()],
                check_pre_post_scripts(summaryfile))

    # Add labels to all metrics
    metrics = [metric.labels == labels for metric in metrics]

    print([string(metric) for metric in metrics])


               