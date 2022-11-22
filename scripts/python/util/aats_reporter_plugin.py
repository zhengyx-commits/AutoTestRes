#!/usr/bin/env python
# Copyright 2021 Amlogic.com, Inc. or its affiliates. All rights reserved.
#
# AMLOGIC PROPRIETARY/CONFIDENTIAL
#
# You may not use this file except in compliance with the terms and conditions
# set forth in the accompanying LICENSE.TXT file.
#
# THESE MATERIALS ARE PROVIDED ON AN "AS IS" BASIS. AMLOGIC SPECIFICALLY
# DISCLAIMS, WITH RESPECT TO THESE MATERIALS, ALL WARRANTIES, EXPRESS,
# IMPLIED, OR STATUTORY, INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
#
import os
import pytest
import logging
from _pytest.terminal import TerminalReporter
from protocol.aats.exceptions import (AATSBinaryMissingError,
                                      AATSInvalidTestPathException,
                                      AATSTimeoutException)
from util.logger import LTPLogger


def pytest_runtest_call(__multicall__):
    try:
        __multicall__.execute()
    except Exception as e:
        logging.exception(e)
        raise


@pytest.mark.trylast
def pytest_configure(config):
    # Get the standard terminal reporter plugin...
    standard_reporter = config.pluginmanager.getplugin('terminalreporter')
    reporter = AATSTerminalReporter(standard_reporter)

    # ...and replace it with our own instafailing reporter.
    config.pluginmanager.unregister(standard_reporter)
    config.pluginmanager.register(reporter, 'terminalreporter')

    for test_path in config.option.file_or_dir:
        if "::" in test_path:
            test_path = test_path.split("::")[0]
        if not os.path.exists(test_path):
            pytest.result.log_brok("Given test path does not exist: %s" % test_path)
            raise AATSInvalidTestPathException("Given test path does not exist: %s" % test_path)


class AATSTerminalReporter(TerminalReporter):
    AATS_EXCEPTIONS_SKIP = [AATSBinaryMissingError]
    AATS_EXCEPTIONS_BROK = [AATSTimeoutException]

    def __init__(self, reporter):
        TerminalReporter.__init__(self, reporter.config)
        self._tw = reporter._tw
        pytest.result = LTPLogger("AATSTest")
        try:
            self._sessionstarttime = reporter._sessionstarttime
        except:
            pass

    def write_line(self, line, **markup):
        logging.debug(line)
        return super().write_line(line, **markup)

    def pytest_runtest_logstart(self, nodeid, location):
        # ensure that the path is printed before the
        # 1st test of a module starts running
        logging.debug('{title:{char}^{length}}'.format(title=' runtest start ', length=80, char='='))
        logging.debug(nodeid)
        pytest.result.set_name(nodeid.split("::")[1])
        if self.showlongtestinfo:
            line = self._locationline(nodeid, *location)
            self.write_ensure_prefix(line, "\n")
        elif self.showfspath:
            fsid = nodeid.split("::")[0]
            self.write_fspath_result(fsid, "\n")

    def pytest_sessionstart(self, session):
        logging.debug('{title:{char}^{length}}'.format(title=' live log sessionstart ', length=80, char='-'))
        super(AATSTerminalReporter, self).pytest_sessionstart(session)

    def pytest_runtest_setup(self):
        logging.debug('{title:{char}^{length}}'.format(title=' live log setup ', length=80, char='-'))

    def pytest_runtest_teardown(self):
        logging.debug('{title:{char}^{length}}'.format(title=' live log teardown ', length=80, char='-'))

    def pytest_sessionfinish(self, exitstatus):
        logging.debug('{title:{char}^{length}}'.format(title=' live log sessionfinish ', length=80, char='-'))
        # super(AATSTerminalReporter, self).pytest_sessionfinish(exitstatus)

    def pytest_runtest_call(self):
        logging.debug('{title:{char}^{length}}'.format(title=' live log call ', length=80, char='-'))

    def pytest_collectreport(self, report):
        # Show errors occurred during the collection instantly.
        TerminalReporter.pytest_collectreport(self, report)
        if report.failed:
            self.rewrite("")  # erase the "collecting" message
            msg = "Error collecting {}".format(
                self._getfailureheadline(report))
            try:
                pytest.result.log_brok(msg)
            except:
                pass
            self.print_failure(report)

    def pytest_runtest_logreport(self, report):
        # Show failures and errors occuring during running a test
        # instantly.
        if (report.when != 'call') and report.outcome == 'passed':
            return

        cat, letter, word = self.config.hook.pytest_report_teststatus(
            report=report,
            config=self.config)
        self.stats.setdefault(cat, []).append(report)
        self._tests_ran = True
        if report.failed and not hasattr(report, 'wasxfail'):
            if self.verbosity <= 0:
                self._tw.line()
            line = self._getcrashline(report)
            msg = line.split(os.getcwd())[-1].lstrip('/')
            self.print_failure(report)
            # All the exceptions thrown from AATS result in a test failure.
            # Certain AATS exceptions however are actually issues in the
            # test environment and need to be marked as 'skipped' instead
            # of 'failed.'
            # Similarly, AATS timeout exceptions will be reported with 'BROK.'
            if any(exception.__name__ in msg
                   for exception in self.AATS_EXCEPTIONS_SKIP):
                pytest.result.log_skip(msg)
            elif any(exception.__name__ in msg
                     for exception in self.AATS_EXCEPTIONS_BROK):
                pytest.result.log_brok(msg)
            else:
                pytest.result.log_fail(msg)
        elif report.passed:
            # if pytest.result.log_auto_pass:
            msg = 'Test Passed'
            pytest.result.log_pass(msg)
        elif report.outcome == 'skipped':
            msg = "Test Skipped."
            if report.longrepr:
                try:
                    msg = report.longrepr[2]
                except:
                    pass
            pytest.result.log_skip(msg)
        logging.debug('{title:{char}^{length}}'.format(title=' runtest finish ', length=80, char='='))

    def summary_fialures(self):
        # Prevent failure summary from being shown since we already
        # show the failure instantly after failure has occured.
        pass

    def summary_errors(self):
        # Prevent error summary from being shown since we already
        # show the error instantly after error has occured.
        pass

    def print_failure(self, report):
        if self.config.option.tbstyle != "no":
            if self.config.option.tbstyle == "line":
                line = self._getcrashline(report)
                self.write_line(line)
            else:
                msg = self._getfailureheadline(report)
                if not hasattr(report, 'when'):
                    msg = "ERROR collecting " + msg
                elif report.when == "setup":
                    msg = "ERROR at setup of " + msg
                elif report.when == "teardown":
                    msg = "ERROR at teardown of " + msg
                self.write_sep("_", msg)
                # Todo
                if not self.config.getvalue("usepdb"):
                    self._outrep_summary(report)
