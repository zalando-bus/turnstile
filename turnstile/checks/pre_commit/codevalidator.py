#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import subprocess
import re

import turnstile.checks as checks
import turnstile.common.output as output


def codevalidator(files_to_check, temporary_dir=None, custom_config=None, fix=False):
    """
    Wrapper around codevalidator

    :param files_to_check: list of files to check
    :type files_to_check: list
    :param temporary_dir: temporary dir used, this is used to remove it from the output
    :param custom_config: path to custom codevalidatorrc if any
    :type custom_config: pathlib.Path
    :param fix: whether to try to fix the files or not
    :type fix: bool
    :return: codevalidator output
    """

    logger = output.get_sub_logger('pre-commit', 'codevalidator')

    arguments = ['codevalidator', '-v']
    arguments.extend(str(path) for path in files_to_check)

    if custom_config.is_file:
        arguments.extend(['-c', str(custom_config.resolve())])

    if fix:
        arguments.append('-f')

    logger.debug('Command Arguments: %s', arguments)

    process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    logger.debug('Standard Output: %s', stdout)
    logger.debug('Standard Error: %s', stderr)

    codevalidator_output = stdout + stderr

    if temporary_dir:
        codevalidator_output = remove_temporary_path(codevalidator_output, temporary_dir)

    return codevalidator_output


def remove_temporary_path(codevalidator_output, temporary__dir_path):
    """
    Removes the temporary dir path from the file paths

    >>> remove_temporary_path('/tmp/test/file.a ERROR', '/tmp/test')
    'file.a ERROR'

    :param codevalidator_output: Raw codevalidator output
    :type codevalidator_output: str
    :param temporary__dir_path:
    :type temporary__dir_path: pathlib.Path
    :return: codevalidator_output with paths relative to the root directory
    """

    regular_expression = '^{temp_dir}/'.format(temp_dir=re.escape(str(temporary__dir_path)))
    regex = re.compile(regular_expression)
    lines = [regex.sub('', line, 1) for line in codevalidator_output.splitlines()]
    return '\n'.join(lines)


@checks.Check('Codevalidator Check')
def check(user_configuration, repository_configuration, staging_area):
    """
    Codevalidator check

    :param user_configuration: User specific configuration
    :type user_configuration: git_hooks.common.config.UserConfiguration
    :param repository_configuration: Repository specific configuration
    :type repository_configuration: dict
    :param staging_area:
    :type staging_area: git_hooks.models.staging.StagingArea
    :return: If check passed or not
    :rtype: turnstile.checks.CheckResult
    """

    result = checks.CheckResult()

    logger = output.get_sub_logger('pre-commit', 'codevalidator')
    logger.debug('Starting Codevalidator check...')
    if not staging_area.changes:
        logger.debug('No files to check.')
        raise checks.CheckIgnore

    codevalidator_rc = staging_area.working_dir / '.codevalidatorrc'

    with staging_area:
        codevalidator_output = codevalidator(files_to_check=staging_area.files,
                                             temporary_dir=staging_area.temporary_directory,
                                             custom_config=codevalidator_rc)
        result.successful = not codevalidator_output
        if not result.successful:
            result.details.append(codevalidator_output)

    return result
