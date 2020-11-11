"""
Tool functions for CloudFormation scripts.
"""

import boto3
import time
import progressbar


def monitor_stack_deployment(cf_session, stack_name):

    stack_in_progress = [
        'CREATE_IN_PROGRESS',
        'ROLLBACK_IN_PROGRESS',
        'DELETE_IN_PROGRESS',
        'UPDATE_IN_PROGRESS',
        'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
        'UPDATE_ROLLBACK_IN_PROGRESS',
        'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
        'REVIEW_IN_PROGRESS',
        'IMPORT_IN_PROGRESS',
        'IMPORT_ROLLBACK_IN_PROGRESS',
    ]

    stack_complete = [
        'CREATE_COMPLETE',
        'ROLLBACK_COMPLETE',
        'DELETE_COMPLETE',
        'UPDATE_COMPLETE',
        'UPDATE_ROLLBACK_COMPLETE',
        'IMPORT_COMPLETE',
        'IMPORT_ROLLBACK_COMPLETE'
    ]

    stack_failed = [
        'CREATE_FAILED',
        'ROLLBACK_FAILED',
        'DELETE_FAILED',
        'UPDATE_ROLLBACK_FAILED',
        'IMPORT_ROLLBACK_FAILED',
    ]

    widgets = [
        progressbar.BouncingBar(), ' ',
        progressbar.Timer()
    ]
    bar = progressbar.ProgressBar(
        widgets=widgets,
        max_value=progressbar.UnknownLength,
        prefix='Waiting for stack deployment to complete ... '
    )
    progress_steps = 1
    done = False
    while not done:
        time.sleep(5)
        response = cf_session.describe_stacks(StackName=stack_name)
        bar.update(progress_steps)
        progress_steps += 1
        stack_status = response['Stacks'][0]['StackStatus']
        done = stack_status in stack_complete or stack_status in stack_failed
    bar.finish()
    return stack_status
